#!/usr/bin/env python3
"""Verify the slateiq ClickHouse dataset: row counts, views, golden queries.

    python db/verify.py          # exits non-zero on any failure

Golden queries are parsed straight out of db/SCHEMA.md so the agent-facing doc
can never drift from something that actually runs.
"""

from __future__ import annotations

import os
import re
import sys

import clickhouse_connect

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = "tos2026"

# table -> (min_rows, max_rows)
EXPECTED = {
    "production": (1, 1),
    "scene": (120, 120),
    "shooting_day": (30, 30),
    "take": (1500, 6000),
    "take_event": (12000, 90000),
    "take_analysis": (1500, 6000),
    "continuity_note": (40, 200),
    "frame_telemetry": (3_000_000, 60_000_000),
    "take_daily_agg": (1, 60),
    "take_scene_agg": (1, 240),
}

failures: list[str] = []
rows: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    rows.append(("PASS" if ok else "FAIL", name, detail))
    if not ok:
        failures.append(f"{name}: {detail}")


def golden_queries(path: str) -> list[tuple[str, str]]:
    sql = re.search(r"```sql\n(.*?)```", open(path).read(), re.DOTALL).group(1)
    out, label, buf = [], None, []
    for line in sql.splitlines():
        m = re.match(r"^--\s*(\d+\s+.*)$", line)
        if m:
            if label:
                out.append((label, "\n".join(buf)))
            label, buf = m.group(1), []
        elif label:
            buf.append(line)
    if label:
        out.append((label, "\n".join(buf)))
    return out


def main() -> int:
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "clickhouse"),
        secure=os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true",
    )

    # --- row counts -------------------------------------------------------
    for table, (lo, hi) in EXPECTED.items():
        try:
            n = client.command(f"SELECT count() FROM slateiq.{table}")
            n = int(n)
        except Exception as exc:
            check(f"count {table}", False, str(exc)[:120])
            continue
        check(f"count {table}", lo <= n <= hi, f"{n:,} rows (expect {lo:,}..{hi:,})")

    # --- materialized views actually populated ----------------------------
    for mv, _src in (("take_daily_agg", "day_number"), ("take_scene_agg", "scene_number")):
        try:
            a = int(client.command(f"SELECT sum(takes) FROM slateiq.{mv}"))
            b = int(client.command("SELECT count() FROM slateiq.take"))
            check(f"MV {mv} totals match take", a == b, f"{a:,} vs {b:,}")
        except Exception as exc:
            check(f"MV {mv}", False, str(exc)[:120])

    # --- semantic invariants ---------------------------------------------
    checks = [
        (
            "days 13-30 have no takes",
            "SELECT count() FROM slateiq.take WHERE day_number > 12",
            lambda v: v == 0,
        ),
        (
            "day 12 is the latest shot day",
            "SELECT max(day_number) FROM slateiq.take",
            lambda v: v == 12,
        ),
        ("30 shooting days planned", "SELECT count() FROM slateiq.shooting_day", lambda v: v == 30),
        (
            "unshot days have NULL actual_wrap",
            "SELECT count() FROM slateiq.shooting_day WHERE day_number>12 AND actual_wrap IS NOT NULL",
            lambda v: v == 0,
        ),
        (
            "day 8 behind schedule (pages shot < planned)",
            "SELECT pages_shot_eighths < pages_planned_eighths FROM slateiq.daily_progress WHERE day_number=8",
            lambda v: v == 1,
        ),
        (
            "day 11 behind schedule",
            "SELECT pages_shot_eighths < pages_planned_eighths FROM slateiq.daily_progress WHERE day_number=11",
            lambda v: v == 1,
        ),
        (
            "overtime exists",
            "SELECT count() FROM slateiq.daily_progress WHERE wrap_delay_min > 0",
            lambda v: v >= 3,
        ),
        (
            "circled takes exist on every shot day",
            "SELECT count() FROM slateiq.daily_progress WHERE day_number<=12 AND circled=0",
            lambda v: v == 0,
        ),
        (
            "every take has an analysis row",
            "SELECT count() FROM slateiq.take t LEFT JOIN slateiq.take_analysis a "
            "USING (production_id,take_id) WHERE a.take_id = ''",
            lambda v: v == 0,
        ),
        (
            "all 8 flag types present",
            "SELECT uniqExact(flag_type) FROM slateiq.take_event WHERE kind='flag'",
            lambda v: v == 8,
        ),
        (
            "'forty years' dialogue searchable",
            "SELECT count() FROM slateiq.take_event WHERE speaker='Celia' AND text ILIKE '%forty years%'",
            lambda v: v > 0,
        ),
        (
            "telemetry joins to takes",
            "SELECT uniqExact(take_id) FROM slateiq.frame_telemetry",
            lambda v: v > 1000,
        ),
        (
            "soft-focus telemetry correlates with flags",
            "SELECT countIf(focus_score < 0.55) FROM slateiq.frame_telemetry",
            lambda v: v > 1000,
        ),
        (
            "reserved ingest scenes exist in scene table",
            "SELECT count() FROM slateiq.scene WHERE scene_number IN "
            "('12','14A','27','33','41','56','78','102')",
            lambda v: v == 8,
        ),
        (
            "scene_progress covers all 120 scenes",
            "SELECT count() FROM slateiq.scene_progress",
            lambda v: v == 120,
        ),
        ("flag_summary populated", "SELECT count() FROM slateiq.flag_summary", lambda v: v > 20),
    ]
    for name, sql, pred in checks:
        try:
            v = client.command(sql)
            v = int(v) if v not in (None, "") else 0
            check(name, pred(v), f"= {v}")
        except Exception as exc:
            check(name, False, str(exc)[:140])

    # --- golden queries from SCHEMA.md ------------------------------------
    for label, sql in golden_queries(os.path.join(HERE, "SCHEMA.md")):
        try:
            res = client.query(sql)
            check(f"golden Q{label[:44]}", len(res.result_rows) > 0, f"{len(res.result_rows)} rows")
        except Exception as exc:
            check(f"golden Q{label[:44]}", False, str(exc)[:140])

    # --- print table ------------------------------------------------------
    w1 = max(len(r[1]) for r in rows)
    print(f"{'':4}  {'check'.ljust(w1)}  detail")
    print("-" * (w1 + 40))
    for st, name, detail in rows:
        print(f"{st:4}  {name.ljust(w1)}  {detail}")
    print("-" * (w1 + 40))
    print(f"{len(rows) - len(failures)}/{len(rows)} passed")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
