-- SlateIQ — ClickHouse data model for a feature-film shoot
-- Database: slateiq   (always query with the `slateiq.` prefix)
-- Conventions: MergeTree everywhere, LowCardinality for enums, no FINAL needed.
-- Ingest is NOT deduplicating: delete-before-insert if you re-ingest a take.

CREATE DATABASE IF NOT EXISTS slateiq;

-- ---------------------------------------------------------------- production
CREATE TABLE IF NOT EXISTS slateiq.production
(
    production_id String,
    title         String,
    start_date    Date,
    planned_days  UInt16,
    director      String,
    dp            String,
    notes         String
)
ENGINE = MergeTree
ORDER BY production_id;

-- --------------------------------------------------------------------- scene
CREATE TABLE IF NOT EXISTS slateiq.scene
(
    production_id String,
    scene_number  String,                       -- '12', '14A' ... string, NOT numeric
    slug          String,                       -- 'INT. LAB - NIGHT'
    int_ext       LowCardinality(String),       -- 'INT' | 'EXT'
    day_night     LowCardinality(String),       -- 'DAY' | 'NIGHT' | 'DUSK' | 'DAWN'
    page_eighths  UInt16,                       -- script length in 1/8 pages (pages = /8.0)
    synopsis      String,
    characters    Array(String),
    location      String,
    script_day    UInt8,                        -- story day
    est_setups    UInt8
)
ENGINE = MergeTree
ORDER BY (production_id, scene_number);

-- ------------------------------------------------------------- shooting_day
CREATE TABLE IF NOT EXISTS slateiq.shooting_day
(
    production_id   String,
    day_number      UInt16,                     -- 1..30
    shoot_date      Date,
    unit            LowCardinality(String),     -- 'main' | 'second'
    call_time       DateTime,
    planned_wrap    DateTime,
    actual_wrap     Nullable(DateTime),         -- NULL => day not shot yet (day > 12)
    planned_scenes  Array(String),
    location        String,
    weather         String,
    notes           String
)
ENGINE = MergeTree
ORDER BY (production_id, day_number);

-- ---------------------------------------------------------------------- take
CREATE TABLE IF NOT EXISTS slateiq.take
(
    production_id String,
    take_id       String,                       -- 'TOS-D07-S23-B-04' (unique)
    day_number    UInt16,
    scene_number  String,
    shot          String,                       -- setup letter: 'A','B','C',...
    take_number   UInt8,
    camera        LowCardinality(String),       -- 'A' | 'B' | 'C'
    roll          String,
    sound_roll    String,
    clip_uri      String,
    thumb_uri     String,
    tc_in         String,                       -- 'HH:MM:SS:FF' @25fps
    duration_s    Float32,
    status        LowCardinality(String),       -- circled|ng|hold|wild|pending
    director_note String,
    lens_mm       UInt16,
    fps           UInt8,
    iso           UInt16,
    created_at    DateTime
)
ENGINE = MergeTree
ORDER BY (production_id, day_number, scene_number, shot, take_number, camera);

-- --------------------------------------------------------------- take_event
CREATE TABLE IF NOT EXISTS slateiq.take_event
(
    production_id String,
    take_id       String,
    event_id      String,
    t_offset_s    Float32,                      -- seconds from head of clip
    t_end_s       Float32,
    kind          LowCardinality(String),       -- dialogue|action|flag|slate|emotion|camera
    speaker       String,                       -- character name for dialogue/emotion, else ''
    text          String,
    flag_type     LowCardinality(String),       -- soft_focus|boom_in_shot|line_flub|overlap|
                                                -- continuity|frame_edge|audio_clip|crew_in_shot|''
    severity      UInt8,                        -- 1..5, 0 for non-flags
    score         Float32,                      -- emotion intensity / confidence 0..1
    meta          String                        -- free JSON
)
ENGINE = MergeTree
ORDER BY (production_id, take_id, t_offset_s, event_id);

-- ------------------------------------------------------------ take_analysis
CREATE TABLE IF NOT EXISTS slateiq.take_analysis
(
    production_id     String,
    take_id           String,
    summary           String,
    transcript        String,
    quality_score     Float32,                  -- 0..1 technical+performance blend
    recommended       Bool,
    emotion_intensity Float32,                  -- 0..1
    performance_note  String,
    model             String,
    analyzed_at       DateTime
)
ENGINE = MergeTree
ORDER BY (production_id, take_id);

-- ---------------------------------------------------------- continuity_note
CREATE TABLE IF NOT EXISTS slateiq.continuity_note
(
    production_id String,
    scene_number  String,
    take_id_a     String,
    take_id_b     String,
    category      LowCardinality(String),       -- wardrobe|props|hair_makeup|screen_direction|
                                                -- lighting|action_match|dialogue|set_dressing
    description   String,
    severity      UInt8,                        -- 1..5
    created_at    DateTime
)
ENGINE = MergeTree
ORDER BY (production_id, scene_number, created_at);

-- --------------------------------------------------------- frame_telemetry
-- BIG table: one row per sampled frame (25 Hz) per take. Millions of rows.
CREATE TABLE IF NOT EXISTS slateiq.frame_telemetry
(
    production_id String,
    take_id       String,
    t_s           Float32 CODEC(Gorilla, ZSTD(1)),
    focus_score   Float32 CODEC(Gorilla, ZSTD(1)),   -- 0..1, <0.55 = soft
    exposure_ev   Float32 CODEC(Gorilla, ZSTD(1)),   -- stops from key
    motion        Float32 CODEC(Gorilla, ZSTD(1)),   -- 0..1 frame motion energy
    audio_peak_db Float32 CODEC(Gorilla, ZSTD(1)),   -- dBFS, >-3 = clipping risk
    audio_rms_db  Float32 CODEC(Gorilla, ZSTD(1))
)
ENGINE = MergeTree
ORDER BY (production_id, take_id, t_s);

-- =================================================================
-- Aggregating tables + materialized views (fed automatically on INSERT INTO take)
-- =================================================================
CREATE TABLE IF NOT EXISTS slateiq.take_daily_agg
(
    production_id  String,
    day_number     UInt16,
    takes          SimpleAggregateFunction(sum, UInt64),
    circled        SimpleAggregateFunction(sum, UInt64),
    ng             SimpleAggregateFunction(sum, UInt64),
    camera_seconds SimpleAggregateFunction(sum, Float64),
    setups         AggregateFunction(uniq, String)
)
ENGINE = AggregatingMergeTree
ORDER BY (production_id, day_number);

CREATE MATERIALIZED VIEW IF NOT EXISTS slateiq.mv_take_daily_agg
TO slateiq.take_daily_agg AS
SELECT production_id,
       day_number,
       count()                                    AS takes,
       countIf(status = 'circled')                AS circled,
       countIf(status = 'ng')                     AS ng,
       sum(toFloat64(duration_s))                 AS camera_seconds,
       uniqState(concat(scene_number, '/', shot)) AS setups
FROM slateiq.take
GROUP BY production_id, day_number;

CREATE TABLE IF NOT EXISTS slateiq.take_scene_agg
(
    production_id  String,
    scene_number   String,
    takes          SimpleAggregateFunction(sum, UInt64),
    circled        SimpleAggregateFunction(sum, UInt64),
    ng             SimpleAggregateFunction(sum, UInt64),
    camera_seconds SimpleAggregateFunction(sum, Float64),
    setups         AggregateFunction(uniq, String),
    first_day      SimpleAggregateFunction(min, UInt16),
    last_day       SimpleAggregateFunction(max, UInt16)
)
ENGINE = AggregatingMergeTree
ORDER BY (production_id, scene_number);

CREATE MATERIALIZED VIEW IF NOT EXISTS slateiq.mv_take_scene_agg
TO slateiq.take_scene_agg AS
SELECT production_id,
       scene_number,
       count()                     AS takes,
       countIf(status = 'circled') AS circled,
       countIf(status = 'ng')      AS ng,
       sum(toFloat64(duration_s))  AS camera_seconds,
       uniqState(shot)             AS setups,
       min(day_number)             AS first_day,
       max(day_number)             AS last_day
FROM slateiq.take
GROUP BY production_id, scene_number;

-- ----------------------------------------------------- dashboard views
-- Always-fresh views on top of the aggregates. Query these for dashboards/DPR.

CREATE OR REPLACE VIEW slateiq.daily_progress AS
WITH scene_first_day AS
(
    SELECT production_id, scene_number, min(first_day) AS d, sum(circled) AS c
    FROM slateiq.take_scene_agg GROUP BY production_id, scene_number
),
pages AS
(
    SELECT f.production_id AS production_id, f.d AS day_number,
           sum(s.page_eighths) AS pages_shot_eighths
    FROM scene_first_day f
    INNER JOIN slateiq.scene s
        ON s.production_id = f.production_id AND s.scene_number = f.scene_number
    WHERE f.c > 0
    GROUP BY f.production_id, f.d
),
planned AS
(
    SELECT d.production_id AS production_id, d.day_number AS day_number,
           sum(s.page_eighths) AS pages_planned_eighths
    FROM slateiq.shooting_day d
    ARRAY JOIN d.planned_scenes AS psc
    INNER JOIN slateiq.scene s
        ON s.production_id = d.production_id AND s.scene_number = psc
    GROUP BY d.production_id, d.day_number
)
SELECT d.production_id                                   AS production_id,
       d.day_number                                      AS day_number,
       d.shoot_date                                      AS shoot_date,
       d.unit                                            AS unit,
       ifNull(p.pages_planned_eighths, 0)                AS pages_planned_eighths,
       ifNull(g.pages_shot_eighths, 0)                   AS pages_shot_eighths,
       ifNull(uniqMerge(a.setups), 0)                    AS setups,
       ifNull(sum(a.takes), 0)                           AS takes,
       ifNull(sum(a.circled), 0)                         AS circled,
       ifNull(sum(a.ng), 0)                              AS ng,
       round(ifNull(sum(a.camera_seconds), 0) / 60, 1)   AS camera_minutes,
       if(d.actual_wrap IS NULL, NULL,
          toInt32(dateDiff('minute', d.planned_wrap, assumeNotNull(d.actual_wrap)))) AS wrap_delay_min
FROM slateiq.shooting_day d
LEFT JOIN slateiq.take_daily_agg a
       ON a.production_id = d.production_id AND a.day_number = d.day_number
LEFT JOIN planned p
       ON p.production_id = d.production_id AND p.day_number = d.day_number
LEFT JOIN pages g
       ON g.production_id = d.production_id AND g.day_number = d.day_number
GROUP BY d.production_id, d.day_number, d.shoot_date, d.unit,
         d.planned_wrap, d.actual_wrap,
         p.pages_planned_eighths, g.pages_shot_eighths
ORDER BY d.day_number;

CREATE OR REPLACE VIEW slateiq.scene_progress AS
SELECT s.production_id                                    AS production_id,
       s.scene_number                                     AS scene_number,
       s.slug                                             AS slug,
       s.page_eighths                                     AS page_eighths,
       s.est_setups                                       AS est_setups,
       ifNull(sum(a.takes), 0)                            AS takes,
       ifNull(sum(a.circled), 0)                          AS circled,
       ifNull(uniqMerge(a.setups), 0)                     AS setups,
       min(a.first_day)                                   AS first_day,
       max(a.last_day)                                    AS last_day,
       round(sum(a.takes) / greatest(sum(a.circled), 1), 2) AS shooting_ratio,
       multiIf(sum(a.takes) = 0, 'not_shot',
               sum(a.circled) = 0, 'no_circled',
               uniqMerge(a.setups) < s.est_setups, 'partial',
               'complete')                                AS status
FROM slateiq.scene s
LEFT JOIN slateiq.take_scene_agg a
       ON a.production_id = s.production_id AND a.scene_number = s.scene_number
GROUP BY s.production_id, s.scene_number, s.slug, s.page_eighths, s.est_setups;

CREATE OR REPLACE VIEW slateiq.flag_summary AS
SELECT t.production_id            AS production_id,
       t.day_number               AS day_number,
       e.flag_type                AS flag_type,
       count()                    AS flags,
       uniqExact(e.take_id)       AS takes_affected,
       round(avg(e.severity), 2)  AS avg_severity
FROM slateiq.take_event e
INNER JOIN slateiq.take t
        ON t.production_id = e.production_id AND t.take_id = e.take_id
WHERE e.kind = 'flag' AND e.flag_type != ''
GROUP BY t.production_id, t.day_number, e.flag_type;
