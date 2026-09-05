# SlateIQ ClickHouse schema (db `slateiq`)

One production, `production_id='tos2026'`: *Tears of Steel*, 30 days, Amsterdam.
**Day 12 (2026-09-04) is today.** Days 1-12 shot; days 13-30 scheduled only (no takes).
Always prefix tables with `slateiq.`; one production only, so joins may USING take_id.

## Tables
- production (1) title,start_date,planned_days,director,dp,notes
- scene (120) scene_number String! ('12','14A'), slug, int_ext, day_night, page_eighths, synopsis, characters Array(String), location, script_day, est_setups
- shooting_day (30) day_number, shoot_date, unit, call_time, planned_wrap, actual_wrap (NULL=not shot), planned_scenes Array(String), location, weather, notes
- take (~2.5k) take_id, day_number, scene_number, shot (setup A/B/C), take_number, camera, roll, sound_roll, clip_uri, thumb_uri, tc_in, duration_s, status, director_note, lens_mm, fps, iso, created_at
- take_event (~26k) take_id, event_id, t_offset_s, t_end_s, kind, speaker, text, flag_type, severity 1-5, score, meta
- take_analysis (1/take) take_id, summary, transcript, quality_score 0-1, recommended Bool, emotion_intensity, performance_note, model
- continuity_note (60) scene_number, take_id_a, take_id_b, category, description, severity
- frame_telemetry (3M+ rows, 25/s/take) take_id, t_s, focus_score 0-1, exposure_ev, motion, audio_peak_db dBFS, audio_rms_db

Enums - take.status: circled(=selected)|ng|hold|wild|pending.
take_event.kind: dialogue|action|flag|slate|emotion|camera.
take_event.flag_type: soft_focus|boom_in_shot|line_flub|overlap|continuity|frame_edge|audio_clip|crew_in_shot|''.
continuity_note.category: wardrobe|props|hair_makeup|screen_direction|lighting|action_match|dialogue|set_dressing.

Joins - take.take_id -> take_event/take_analysis/frame_telemetry/continuity_note.take_id_a|_b; take.scene_number -> scene; take.day_number -> shooting_day.

## Views (pre-aggregated - prefer these for reports)
- daily_progress per day: pages_planned_eighths, pages_shot_eighths, setups, takes, circled, ng, camera_minutes, wrap_delay_min
- scene_progress per scene: takes, circled, setups, first_day, last_day, shooting_ratio, status (not_shot|no_circled|partial|complete)
- flag_summary per day+flag_type: flags, takes_affected, avg_severity

## Gotchas
- page_eighths/8.0 = script pages. scene_number is never numeric ('14A').
- Shooting ratio = takes/circled (higher = more film burned); guard greatest(circled,1).
- A take row is one camera's slate: a 2-cam setup = 2 rows. Setups = uniq(scene_number,shot).
- Days 8 & 11 lost setups to rain: pages_shot < pages_planned, some planned scenes have no takes.
- Scenes 12,14A,27,33,41,56,78,102 are day-12 scenes fed by the real-clip ingest.
- wrap_delay_min>0 = overtime; NULL on unshot days. No FINAL needed.
- Useful: ILIKE, has(characters,'Celia'), ARRAY JOIN planned_scenes, countIf().

## Golden questions
```sql
-- 1 EDITOR best takes for a scene
SELECT t.take_id,a.quality_score,a.performance_note,t.clip_uri
FROM slateiq.take t JOIN slateiq.take_analysis a USING take_id
WHERE t.scene_number='99' AND t.status='circled' ORDER BY a.quality_score DESC LIMIT 5;
-- 2 EDITOR takes where Celia says "forty years"
SELECT e.take_id,t.scene_number,e.t_offset_s,e.text FROM slateiq.take_event e
JOIN slateiq.take t USING take_id
WHERE e.speaker='Celia' AND e.text ILIKE '%forty years%' LIMIT 20;
-- 3 EDITOR takes flagged boom/soft focus today
SELECT e.take_id,e.flag_type,e.severity,e.t_offset_s FROM slateiq.take_event e
JOIN slateiq.take t USING take_id
WHERE t.day_number=12 AND e.flag_type IN ('boom_in_shot','soft_focus') ORDER BY e.severity DESC;
-- 4 EDITOR circled-take list (EDL-ish) for today
SELECT scene_number,shot,take_number,camera,tc_in,duration_s,roll,clip_uri
FROM slateiq.take WHERE day_number=12 AND status='circled' ORDER BY scene_number,shot;
-- 5 SCRIPT SUP continuity conflicts, worst first
SELECT scene_number,category,severity,description FROM slateiq.continuity_note
ORDER BY severity DESC LIMIT 10;
-- 6 SCRIPT SUP scenes with most quality flags
SELECT t.scene_number,count() flags,uniqExact(e.take_id) takes FROM slateiq.take_event e
JOIN slateiq.take t USING take_id WHERE e.kind='flag'
GROUP BY t.scene_number ORDER BY flags DESC LIMIT 10;
-- 7 PRODUCER pages planned vs shot, cumulative
SELECT day_number,pages_planned_eighths/8 planned,pages_shot_eighths/8 shot,
 sum(pages_shot_eighths/8) OVER (ORDER BY day_number) cume FROM slateiq.daily_progress;
-- 8 PRODUCER are we on schedule to date
SELECT sum(pages_planned_eighths)/8 planned,sum(pages_shot_eighths)/8 shot
FROM slateiq.daily_progress WHERE day_number<=12;
-- 9 PRODUCER overtime trend
SELECT day_number,shoot_date,wrap_delay_min FROM slateiq.daily_progress
WHERE wrap_delay_min>0 ORDER BY wrap_delay_min DESC;
-- 10 PRODUCER scenes at risk: planned by today, not shot
SELECT d.day_number,psc AS sc,s.page_eighths/8 pages,s.slug FROM slateiq.shooting_day d
ARRAY JOIN d.planned_scenes AS psc JOIN slateiq.scene s ON s.scene_number=psc
WHERE d.day_number<=12 AND psc NOT IN (SELECT scene_number FROM slateiq.take);
-- 11 PRODUCER camera hours + setups per day
SELECT day_number,setups,takes,camera_minutes/60 cam_hours FROM slateiq.daily_progress WHERE takes>0;
-- 12 DIRECTOR most emotionally intense takes in a scene
SELECT t.take_id,a.emotion_intensity,a.performance_note FROM slateiq.take t
JOIN slateiq.take_analysis a USING take_id
WHERE t.scene_number='7' ORDER BY a.emotion_intensity DESC LIMIT 3;
-- 13 PRODUCER worst shooting ratios
SELECT scene_number,slug,takes,circled,shooting_ratio FROM slateiq.scene_progress
WHERE takes>0 ORDER BY shooting_ratio DESC LIMIT 10;
-- 14 TELEMETRY sustained soft focus (>2s under 0.55), scans 3M rows
SELECT take_id,countIf(focus_score<0.55)/25 soft_s,round(avg(focus_score),3) avg_focus
FROM slateiq.frame_telemetry GROUP BY take_id HAVING soft_s>2 ORDER BY soft_s DESC LIMIT 10;
-- 15 TELEMETRY audio clipping risk per day
SELECT t.day_number,uniqExact(f.take_id) clipping,round(max(f.audio_peak_db),2) worst_peak
FROM slateiq.frame_telemetry f JOIN slateiq.take t USING take_id
WHERE f.audio_peak_db>-3 GROUP BY t.day_number;
```
