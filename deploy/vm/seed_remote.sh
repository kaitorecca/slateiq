#!/usr/bin/env bash
# Seed the hosted ClickHouse on the VM from the LOCAL dev ClickHouse.
#
#   local CH  --(SELECT ... FORMAT Parquet)-->  *.parquet
#             --(gcloud compute scp)-->         VM:/opt/slateiq/seed
#             --(INSERT ... FORMAT Parquet)-->  hosted CH (inside the container)
#
# Parquet is used because it is columnar+compressed (10-30x smaller over the wire than
# TSV for frame_telemetry) and ClickHouse reads it natively on both ends.
#
# The e2-micro has 1 GiB RAM and CH is capped at 400 MiB per query, so big tables are
# streamed in take_id ranges: export -> ship -> insert -> delete, one chunk at a time.
# Peak local disk, VM disk and VM RAM all stay bounded regardless of table size.
#
# Usage:
#   ./seed_remote.sh                      # all tables in the slateiq database
#   ./seed_remote.sh take take_event      # only these tables
#   DRY_RUN=1 ./seed_remote.sh            # print what would happen
#   SCHEMA_ONLY=1 ./seed_remote.sh        # replay DDL only (e.g. a view definition changed)
#   CHUNK_ROWS=200000 ./seed_remote.sh    # smaller chunks if the VM OOMs
set -euo pipefail
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

# ---- local source ------------------------------------------------------------
LOCAL_URL="${LOCAL_CH_URL:-http://localhost:8123}"
LOCAL_USER="${LOCAL_CH_USER:-default}"
LOCAL_PASS="${LOCAL_CH_PASSWORD:-clickhouse}"
DB="${CH_DB:-slateiq}"

# ---- remote target -----------------------------------------------------------
PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
ZONE="${ZONE:-us-central1-a}"
VM="${VM:-slateiq-data}"
STACK_DIR=/opt/slateiq
SEED_DIR="$STACK_DIR/seed"

# Tables that are too big to move in one shot, and the column to range over.
BIG_TABLES="${BIG_TABLES:-frame_telemetry take_event}"
CHUNK_KEY="${CHUNK_KEY:-take_id}"        # hashed, so any type works (ours is a String id)
CHUNK_ROWS="${CHUNK_ROWS:-400000}"       # target rows per chunk; lower this if the VM OOMs
DRY_RUN="${DRY_RUN:-0}"
SCHEMA_ONLY="${SCHEMA_ONLY:-0}"          # 1 = replay DDL and stop (views changed, data did not)

WORK="${WORK:-$REPO_ROOT/data/seed_export}"
mkdir -p "$WORK"

lq()  { curl -sS -f --max-time 600 "$LOCAL_URL/?database=$DB" --user "$LOCAL_USER:$LOCAL_PASS" --data-binary "$1"; }
gssh(){ gcloud compute ssh "$VM" --zone "$ZONE" --project "$PROJECT" --quiet --command "$1" < /dev/null; }
# Run a query on the hosted CH as the admin user, inside the container (never over the internet).
rq()  { gssh "cd $STACK_DIR && set -a && . ./.env && set +a && docker compose exec -T clickhouse clickhouse-client --user default --password \"\$CH_DEFAULT_PASSWORD\" --query \"$1\" < /dev/null"; }

echo "=== SlateIQ remote seed: $LOCAL_URL/$DB  ->  $VM:$STACK_DIR"

# ---------------------------------------------------------------- 0. sanity
lq 'SELECT 1' >/dev/null || { echo "local ClickHouse unreachable at $LOCAL_URL"; exit 1; }

# Materialized-view TARGET tables (take_daily_agg, take_scene_agg, ...) must NOT be copied:
# they are AggregatingMergeTree state that the MVs rebuild themselves when we insert into the
# base tables. Copying them as well would double-count every aggregate.
MV_TARGETS=$(lq "SELECT DISTINCT extract(create_table_query, 'TO ${DB}\\.\`?([A-Za-z0-9_]+)') \
                 FROM system.tables WHERE database='$DB' AND engine='MaterializedView'" | tr '\n' ' ')
echo "mv target tables (skipped, repopulated by the MVs): ${MV_TARGETS:-none}"

# Insert order matters: base tables first so the MVs fire against a populated parent,
# and dimensions before facts so any JOIN-based MV sees its lookups.
SEED_ORDER="${SEED_ORDER:-production scene shooting_day take take_analysis take_event continuity_note camera_metadata frame_telemetry}"

TABLES="${*:-}"
if [ -z "$TABLES" ]; then
  ALL=$(lq "SELECT name FROM system.tables WHERE database='$DB' AND engine NOT LIKE '%View' ORDER BY name" | tr '\n' ' ')
  # SEED_ORDER first (those that exist), then anything else alphabetically.
  TABLES=""
  for t in $SEED_ORDER;  do echo " $ALL " | grep -q " $t " && TABLES="$TABLES $t"; done
  for t in $ALL; do echo " $TABLES " | grep -q " $t " || TABLES="$TABLES $t"; done
fi
# Drop MV targets from whatever list we ended up with.
KEEP=""
for t in $TABLES; do
  if echo " $MV_TARGETS " | grep -q " $t "; then echo "  skip $t (materialized-view target)"; else KEEP="$KEEP $t"; fi
done
TABLES="$KEEP"
[ -n "$TABLES" ] || { echo "no tables found in $DB — has the data engineer created them yet?"; exit 1; }
echo "seed order:$TABLES"

# ---------------------------------------------------------------- 1. schema
# Replay the local DDL on the VM (database + every table + every materialized view),
# so the hosted schema is byte-identical to what the agent was developed against.
echo "--- replaying schema"
[ "$DRY_RUN" = 1 ] || rq "CREATE DATABASE IF NOT EXISTS $DB"
DDL_FILE="$WORK/schema.sql"
# create_table_query carries an Atomic-database UUID; strip it so the remote assigns its own,
# and make every statement idempotent. Base tables are ordered before views so a materialized
# view never references a table that does not exist yet.
# Plain views get CREATE OR REPLACE (their definitions evolve — e.g. scene_progress.print_ratio);
# tables and materialized views get IF NOT EXISTS so existing data is never dropped.
lq "SELECT replaceRegexpOne(replaceRegexpOne(
             replaceRegexpOne(create_table_query, ' UUID \\'[^\\']*\\'', ''),
             '^CREATE (TABLE|MATERIALIZED VIEW|DICTIONARY) ',
             'CREATE \\1 IF NOT EXISTS '), '^CREATE VIEW ', 'CREATE OR REPLACE VIEW ') || ';'
    FROM system.tables WHERE database='$DB' ORDER BY engine LIKE '%View', name
    FORMAT TSVRaw" > "$DDL_FILE"
wc -l "$DDL_FILE"
if [ "$DRY_RUN" != 1 ]; then
  gcloud compute scp "$DDL_FILE" "$VM:$SEED_DIR/schema.sql" --zone "$ZONE" --project "$PROJECT" --quiet
  gssh "cd $STACK_DIR && set -a && . ./.env && set +a && docker compose exec -T clickhouse \
        clickhouse-client --user default --password \"\$CH_DEFAULT_PASSWORD\" --database $DB \
        --multiquery --queries-file /seed/schema.sql < /dev/null"
fi

if [ "$SCHEMA_ONLY" = 1 ]; then
  echo "=== SCHEMA_ONLY: DDL replayed, no data moved"
  exit 0
fi

# Clear any stale aggregate state before the MVs refill it — but ONLY on a full run.
# On a partial run (explicit table args) the MVs would not see the other base tables again,
# so truncating the aggregates would leave them permanently incomplete.
if [ $# -eq 0 ]; then
  for t in $MV_TARGETS; do [ "$DRY_RUN" = 1 ] || rq "TRUNCATE TABLE IF EXISTS $DB.$t"; done
else
  echo "--- partial run: leaving materialized-view aggregates untouched"
fi

# ---------------------------------------------------------------- 2. data
ship_chunk() {           # $1=table  $2=where-clause  $3=label
  local t="$1" where="$2" label="$3"
  local f="$WORK/${t}_${label}.parquet"
  echo "    export $t [$label]"
  if [ "$DRY_RUN" = 1 ]; then echo "DRY: SELECT * FROM $t WHERE $where FORMAT Parquet"; return; fi
  # output_format_parquet_compression_method=zstd keeps the wire small.
  curl -sS -f --max-time 1800 \
    "$LOCAL_URL/?database=$DB&output_format_parquet_compression_method=zstd&max_block_size=65536" \
    --user "$LOCAL_USER:$LOCAL_PASS" \
    --data-binary "SELECT * FROM $t WHERE $where FORMAT Parquet" -o "$f"
  local sz; sz=$(du -h "$f" | cut -f1); echo "      $sz -> shipping"
  gcloud compute scp "$f" "$VM:$SEED_DIR/$(basename "$f")" --zone "$ZONE" --project "$PROJECT" --quiet
  rm -f "$f"
  gssh "cd $STACK_DIR && set -a && . ./.env && set +a && \
        docker compose exec -T clickhouse clickhouse-client --user default --password \"\$CH_DEFAULT_PASSWORD\" \
          --database $DB \
          --max_insert_block_size 65536 --min_insert_block_size_rows 65536 \
          --max_memory_usage 400000000 --max_threads 2 \
          --input_format_parquet_allow_missing_columns 1 \
          --query \"INSERT INTO $t FROM INFILE '/seed/$(basename "$f")' FORMAT Parquet\" < /dev/null && \
        rm -f $SEED_DIR/$(basename "$f")"
}

for t in $TABLES; do
  rows=$(lq "SELECT count() FROM $t")
  echo "--- $t ($rows rows)"
  if [ "$rows" = "0" ]; then echo "    empty, skip"; continue; fi
  [ "$DRY_RUN" = 1 ] || rq "TRUNCATE TABLE IF EXISTS $DB.$t"

  if echo " $BIG_TABLES " | grep -q " $t " && [ "$rows" -gt "$CHUNK_ROWS" ]; then
    # Hash-modulo chunking: works for String ids (ours are like TOS-D12-S102-A-01-A), needs no
    # ORDER BY, and gives evenly sized chunks. Each chunk is exported, shipped, inserted and
    # deleted before the next starts, so local disk, VM disk and VM RAM stay flat.
    key="$CHUNK_KEY"
    has_key=$(lq "SELECT count() FROM system.columns WHERE database='$DB' AND table='$t' AND name='$CHUNK_KEY'")
    [ "$has_key" = "1" ] || key="tuple(*)"
    n=$(( (rows + CHUNK_ROWS - 1) / CHUNK_ROWS ))
    echo "    $rows rows -> $n chunks of ~$CHUNK_ROWS, hashed on $key"
    i=0
    while [ "$i" -lt "$n" ]; do
      ship_chunk "$t" "cityHash64($key) % $n = $i" "p$i"
      i=$((i + 1))
    done
    continue
  fi
  ship_chunk "$t" "1" "all"
done

# ---------------------------------------------------------------- 3. verify
echo "=== row-count comparison (local vs hosted)"
for t in $TABLES $MV_TARGETS; do
  l=$(lq "SELECT count() FROM $t")
  r=$(rq "SELECT count() FROM $DB.$t" 2>/dev/null | tr -d '\r\n ')
  mark=$([ "$l" = "$r" ] && echo OK || echo MISMATCH)
  printf '  %-24s local=%-12s hosted=%-12s %s\n' "$t" "$l" "$r" "$mark"
done
echo "=== done. Hosted CH disk usage:"
rq "SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE database='$DB' AND active"
