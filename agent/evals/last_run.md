# SlateIQ eval — last run

- Run at: 2026-09-05T10:35:45+00:00
- Coordinator model: `gemini-3.5-flash` · report model: `gemini-3.5-flash` · judge: `gemini-3.5-flash`
- ClickHouse MCP: `http://localhost:8765/mcp` (auth: False)
- Questions: **28** · wall clock 615.6s
- Reached MCP `run_query`: **27/27** (100%) — 1 report question(s) served from the on-disk report cache (`dpr`), excluded from the live-query denominator
- Routed to the expected specialist: **27/28**
- Judge score: **mean 4.89/5**, median 5.0, min 3, 27/28 at 4+
- Latency: mean 37.3s, median 26.3s, max 197.3s

| # | id | user | agent(s) | run_query | SQL | takes | score | latency |
|---|---|---|---|---|---|---|---|---|
| 1 | `best_takes_scene` | editor | editor_agent | yes | 1 | 2 | 5 | 13.1s |
| 2 | `dialogue_search` | editor | editor_agent | yes | 8 | 2 | 5 | 28.9s |
| 3 | `boom_in_shot` | editor | editor_agent | yes | 3 | 9 | 3 | 27.4s |
| 4 | `circled_today` | editor | editor_agent | yes | 7 | 12 | 5 | 57.6s |
| 5 | `ng_rate` | editor | production_agent | yes | 10 | 3 | 5 | 37.7s |
| 6 | `on_schedule` | ad | production_agent | yes | 3 | 0 | 5 | 21.6s |
| 7 | `print_ratio` | producer | production_agent | yes | 4 | 0 | 5 | 26.1s |
| 8 | `scenes_at_risk` | ad | production_agent | yes | 10 | 4 | 5 | 46.9s |
| 9 | `overtime_trend` | producer | production_agent | yes | 3 | 0 | 5 | 22.8s |
| 10 | `forecast` | producer | production_agent | yes | 2 | 0 | 5 | 26.5s |
| 11 | `setups_per_day` | ad | production_agent | yes | 3 | 0 | 4 | 17.4s |
| 12 | `continuity_scene` | script_supervisor | continuity_agent | yes | 5 | 2 | 5 | 23.8s |
| 13 | `line_variations` | script_supervisor | continuity_agent | yes | 3 | 2 | 5 | 197.3s |
| 14 | `emotional_intensity` | director | editor_agent | yes | 3 | 4 | 5 | 24.2s |
| 15 | `dpr` | ad | report_agent | cache | 0 | 0 | 5 | 7.2s |
| 16 | `editors_log` | editor | report_agent | yes | 8 | 0 | 5 | 96.0s |
| 17 | `worst_ratio_on_latest_wrap` | producer | editor_agent | yes | 10 | 0 | 5 | 43.6s |
| 18 | `days_over_forecast` | producer | production_agent | yes | 3 | 0 | 5 | 26.2s |
| 19 | `dialogue_across_days` | editor | editor_agent | yes | 5 | 12 | 5 | 30.8s |
| 20 | `focus_compare_takes` | director | editor_agent | yes | 1 | 2 | 5 | 13.0s |
| 21 | `circled_but_soft` | script_supervisor | editor_agent | yes | 1 | 12 | 5 | 26.1s |
| 22 | `telemetry_vs_circled_scene` | director | editor_agent | yes | 10 | 3 | 5 | 54.2s |
| 23 | `rain_scenes_still_unshot` | ad | production_agent | yes | 5 | 0 | 5 | 20.0s |
| 24 | `audio_clipping_day` | editor | editor_agent | yes | 6 | 5 | 5 | 40.4s |
| 25 | `ratio_terminology` | producer | production_agent | yes | 2 | 0 | 5 | 17.4s |
| 26 | `scene_burn_and_flags` | editor | editor_agent | yes | 10 | 0 | 5 | 40.9s |
| 27 | `empty_day` | ad | production_agent | yes | 2 | 0 | 5 | 11.8s |
| 28 | `worst_continuity` | script_supervisor | continuity_agent | yes | 2 | 12 | 5 | 45.6s |

## Detail

### `best_takes_scene` — editor

**Q:** What are the best takes for scene 12?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query  
**Judge:** 5/5 — The agent perfectly answers the question using the database results, detailing the best takes, notes, and scores, and formats the output with the required JSON block containing clip URIs and IDs.  
**Latency:** 13.1s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri,
       a.quality_score, a.recommended, a.performance_note
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.scene_number = '12'
ORDER BY t.status = 'circled' DESC, a.quality_score DESC
LIMIT 50;
```

</details>

<details><summary>Answer</summary>

For Scene 12, we shot two setups (Shot A and Shot B) with a total of 4 takes logged. We have two clear circled takes to cut with:

### Shot A (Wide/Medium Setup)
*   **Take 1 (12/A/1) — KEEPER (Circled)**
    *   **Status:** Circled
    *   **Director's Note:** *"Good energy, keep this one."*
    *   **Quality Score:** 0.85
    *   **Performance Note:** Strong comedic timing and natural chemistry between the actors. The robotic arm prop is handled convincingly.
    *   **Clip:** `clips/TOS-D12-S12-A-01-A.mp4`
*   **Take 2 (12/A/2) — UNUSABLE (NG)**
    *   **Status:** NG
    *   **Director's Note:** *"Focus puller lost her on the turn — NG."*
    *   **Quality Score:** 0.50 (Unusable due to focus issues).

### Shot B (Scope POV / Sniper Setup)
*   **Take 2 (12/B/2) — KEEPER (Circled)**
    *   **Status:** Circled
    *   **Director's Note:** *"Cleaner. Print."*
    *   **Quality Score:** 0.90
    *   **Performance Note:** The transition to the scope POV is clean, and the visual effects tracking of the flying vessel are highly detailed and well-integrated.
    *   **Clip:** `clips/TOS-D12-S12-B-02-B.mp4`
*   **Take 1 (12/B/1) — HOLD**
    *   **Status:** Hold
    *   **Director's Note:** *"Alt angle, hold for editorial."*
    *   **Quality Score:** 0.90
    *   **Performance Note:** Sharp and deliberate movements from the sniper, and the sleeping man's reaction to the searchlight is perfectly timed with the VFX cue.

**Summary for the edit:** Cut **12/A/1** and **12/B/2** together. Keep **12/B/1** in your back pocket as a strong alternative angle for the sniper sequence if needed. Avoid **12/A/2** entirely due to the focus pull error.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-B-02-B",
      "clip_uri": "clips/TOS-D12-S12-B-02-B.mp4",
      "t": 0,
      "label": "12/B/2 circled",
      "reason": "Cleaner. Print. Excellent VFX tracking and scope POV transition."
    },
    {
      "take_id": "TOS-D12-S12-A-01-A",
      "clip_uri": "clips/TOS-D12-S12-A-01-A.mp4",
      "t": 0,
      "label": "12/A/1 circled",
      "reason": "Good energy, keep this one. Strong comedic timing."
    }
  ],
  "sql": [
    "SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri, a.quality_score, a.recommended, a.performance_note FROM slateiq.take t LEFT JOIN slateiq.take_analysis a USING (take_id) WHERE t.scene_number = '12' ORDER BY t.status = 'circled' DESC, a.quality_score DESC LIMIT 50"
  ]
}
```

</details>

---

### `dialogue_search` — editor

**Q:** Find every take where Celia says 'robot hand'. I need the timecode.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly answered the question with all requested details, including speaker, line, and offset, fully grounded in the database results, and added useful production context.  
**Latency:** 28.9s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue'
  AND e.speaker = 'Celia'
  AND e.text ILIKE '%robot hand%'
ORDER BY t.scene_number, t.shot, t.take_number, e.t_offset_s
LIMIT 50;
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue'
  AND e.text ILIKE '%robot%'
ORDER BY t.scene_number, t.shot, t.take_number, e.t_offset_s
LIMIT 50;
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue'
  AND e.text ILIKE '%robot hand%'
ORDER BY t.scene_number, t.shot, t.take_number, e.t_offset_s
LIMIT 50;
SELECT take_id, scene_number, shot, take_number, status, clip_uri
FROM slateiq.take
WHERE scene_number = '12'
ORDER BY shot, take_number
LIMIT 50;
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '12' AND e.kind = 'dialogue'
ORDER BY t.shot, t.take_number, e.t_offset_s
LIMIT 50;
SELECT count() FROM slateiq.take_event WHERE take_id IN ('TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B');
SELECT take_id, kind, speaker, text, t_offset_s FROM slateiq.take_event WHERE take_id IN ('TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B') LIMIT 50;
SELECT t.take_id, t.status, t.director_note, a.quality_score, a.performance_note
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.take_id IN ('TOS-D12-S12-A-01-A', 'TOS-D12-S12-A-02-A');
```

</details>

<details><summary>Answer</summary>

Celia delivers the line **"Why don't you just admit that you're freaked out by my robot hand?"** in exactly two takes from **Scene 12, Shot A**. 

Here are the details and timecodes for both takes:

### 1. **12/A/1** (`TOS-D12-S12-A-01-A`) — **Keeper (Circled)**
* **Timecode Offset:** **5.3 seconds**
* **Status:** Circled
* **Director's Note:** *"Good energy, keep this one."*
* **Performance Note:** Strong comedic timing and natural chemistry between the actors. The robotic arm prop is handled convincingly (Quality Score: **0.85**).
* **Clip:** `clips/TOS-D12-S12-A-01-A.mp4`

### 2. **12/A/2** (`TOS-D12-S12-A-02-A`) — **Unusable (NG)**
* **Timecode Offset:** **5.3 seconds**
* **Status:** NG (No Good)
* **Director's Note:** *"Focus puller lost her on the turn — NG."*
* **Performance Note:** Although the performance was strong, this take is unusable due to focus issues (Quality Score: **0.50**).
* **Clip:** `clips/TOS-D12-S12-A-02-A.mp4`

*Note: Shot B for this scene (`12/B/1` and `12/B/2`) consists of POV scope tracking shots and contains no dialogue.*

**SQL:** I queried `slateiq.take_event` joined with `slateiq.take` for dialogue containing "robot hand" and pulled the corresponding director notes and quality scores from `slateiq.take_analysis`.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-A-01-A",
      "clip_uri": "clips/TOS-D12-S12-A-01-A.mp4",
      "t": 5.3,
      "label": "12/A/1 (Circled)",
      "reason": "Celia: 'Why don't you just admit that you're freaked out by my robot hand?' - Keeper take."
    },
    {
      "take_id": "TOS-D12-S12-A-02-A",
      "clip_uri": "clips/TOS-D12-S12-A-02-A.mp4",
      "t": 5.3,
      "label": "12/A/2 (NG)",
      "reason": "Celia: 'Why don't you just admit that you're freaked out by my robot hand?' - Focus puller lost her."
    }
  ],
  "sql": [
    "SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE e.kind = 'dialogue' AND e.text ILIKE '%robot hand%' ORDER BY t.scene_number, t.shot, t.take_number, e.t_offset_s LIMIT 50",
    "SELECT t.take_id, t.status, t.director_note, a.quality_score, a.performance_note FROM slateiq.take t LEFT JOIN slateiq.take_analysis a USING (take_id) WHERE t.take_id IN ('TOS-D12-S12-A-01-A', 'TOS-D12-S12-A-02-A')"
  ]
}
```

</details>

---

### `boom_in_shot` — editor

**Q:** Which takes have the boom in shot or soft focus problems?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 3/5 — The agent ran the correct initial query but arbitrarily limited its final report to Day 12 takes and failed to group them with counts as required by the rubric.  
**Latency:** 27.4s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT 
    t.take_id,
    t.scene_number,
    t.shot,
    t.take_number,
    t.status,
    t.clip_uri,
    e.flag_type,
    count() as occurrence_count,
    min(e.t_offset_s) as first_offset,
    any(t.director_note) as director_note
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'flag' AND e.flag_type IN ('boom_in_shot', 'soft_focus')
GROUP BY t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.clip_uri, e.flag_type
ORDER BY t.scene_number, t.shot, t.take_number, e.flag_type
LIMIT 100;
SELECT 
    t.day_number,
    e.flag_type,
    count(DISTINCT t.take_id) as takes_affected
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'flag' AND e.flag_type IN ('boom_in_shot', 'soft_focus')
GROUP BY t.day_number, e.flag_type
ORDER BY t.day_number DESC, e.flag_type
LIMIT 100;
SELECT 
    t.take_id,
    t.scene_number,
    t.shot,
    t.take_number,
    t.status,
    t.clip_uri,
    e.flag_type,
    e.severity,
    e.t_offset_s,
    t.director_note
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.day_number = 12 
  AND e.kind = 'flag' 
  AND e.flag_type IN ('boom_in_shot', 'soft_focus')
ORDER BY t.status = 'circled' DESC, t.scene_number, t.shot, t.take_number, e.flag_type
LIMIT 100;
```

</details>

<details><summary>Answer</summary>

On today's shoot (Day 12), we logged **18 takes** with technical flags for either a boom in the shot or soft focus. 

Here are the most critical takes you need to watch out for, starting with the worst offenders (Severity 5, marked NG) and the circled takes we printed anyway that have minor issues.

### Severity 5 (Unusable / NG Takes)
*   **12/A/2** (`TOS-D12-S12-A-02-A`): **Soft focus** at **4.5s**. The focus puller lost her on the turn (NG).
*   **14A/A/2** (`TOS-D12-S14A-A-02-A`): **Boom in shot** at **7.0s**. The boom dipped frame left (NG).
*   **41/A/2** (`TOS-D12-S41-A-02-A`): **Soft focus** at **3.5s**. Soft through the middle (NG for focus).
*   **56/B/2** (`TOS-D12-S56-B-02-B`): **Boom in shot** at **3.0s**. Boom shadow / boom in frame top (NG).
*   **6/C/2** (`TOS-D12-S6-C-02-B`): **Boom in shot** at **9.37s**. Camera bumped the dolly (Hold).

---

### Circled Takes (Printed with Minor Flags)
If you are cutting these circled takes, be aware of these minor dips:
*   **6/D/1** (`TOS-D12-S6-D-01-A`): **Soft focus** at **84.06s** (Severity 3). Note: "one more for safety".
*   **39/B/1** (`TOS-D12-S39-B-01-B`): **Soft focus** at **7.96s** (Severity 2). Note: "focus soft on the turn".
*   **6/A/6** (`TOS-D12-S6-A-06-B`): **Boom in shot** at **13.59s** (Severity 2). Note: "one more for safety".
*   **6/B/3** (`TOS-D12-S6-B-03-C`): **Soft focus** at **29.98s** (Severity 2). Note: "loved the stillness".

SQL: Queried the `take_event` and `take` tables to identify and count takes flagged with `boom_in_shot` or `soft_focus` on Day 12, sorted by severity and circled status.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-A-02-A",
      "clip_uri": "clips/TOS-D12-S12-A-02-A.mp4",
      "t": 4.5,
      "label": "12/A/2 NG",
      "reason": "Focus puller lost her on the turn"
    },
    {
      "take_id": "TOS-D12-S14A-A-02-A",
      "clip_uri": "clips/TOS-D12-S14A-A-02-A.mp4",
      "t": 7.0,
      "label": "14A/A/2 NG",
      "reason": "Boom dipped frame left"
    },
    {
      "take_id": "TOS-D12-S41-A-02-A",
      "clip_uri": "clips/TOS-D12-S41-A-02-A.mp4",
      "t": 3.5,
      "label": "41/A/2 NG",
      "reason": "Soft through the middle"
    },
    {
      "take_id": "TOS-D12-S56-B-02-B",
      "clip_uri": "clips/TOS-D12-S56-B-02-B.mp4",
      "t": 3.0,
      "label": "56/B/2 NG",
      "reason": "Boom shadow / boom in frame top"
    },
    {
      "take_id": "TOS-D12-S6-C-02-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-C-02-B.mp4",
      "t": 9.37,
      "label": "6/C/2 Hold",
      "reason": "Boom in shot / camera bumped dolly"
    },
    {
      "take_id": "TOS-D12-S6-D-01-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-D-01-A.mp4",
      "t": 84.06,
      "label": "6/D/1 Circled",
      "reason": "Soft focus at 84s"
    },
    {
      "take_id": "TOS-D12-S39-B-01-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S39-B-01-B.mp4",
      "t": 7.96,
      "label": "39/B/1 Circled",
      "reason": "Focus soft on the turn"
    },
    {
      "take_id": "TOS-D12-S6-A-06-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-A-06-B.mp4",
      "t": 13.59,
      "label": "6/A/6 Circled",
      "reason": "Boom in shot at 13.6s"
    },
    {
      "take_id": "TOS-D12-S6-B-03-C",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-B-03-C.mp4",
      "t": 29.98,
      "label": "6/B/3 Circled",
      "reason": "Soft focus at 30s"
    }
  ],
  "sql": [
    "SELECT t.day_number, e.flag_type, count(DISTINCT t.take_id) as takes_affected FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE e.kind = 'flag' AND e.flag_type IN ('boom_in_shot', 'soft_focus') GROUP BY t.day_number, e.flag_type ORDER BY t.day_number DESC, e.flag_type LIMIT 100",
    "SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.clip_uri, e.flag_type, e.severity, e.t_offset_s, t.director_note FROM slateiq.take_event e JOIN slateiq.take t USING (tak

…truncated…

</details>

---

### `circled_today` — editor

**Q:** Give me the circled takes from day 12 with the reason each was circled.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly identifies the 38 circled takes for Day 12, lists them by scene/shot/take with director and performance notes, provides the total count, and matches all data returned by the database.  
**Latency:** 57.6s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.clip_uri, t.director_note, a.performance_note, a.summary
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.day_number = 12 AND t.status = 'circled'
ORDER BY t.scene_number, t.shot, t.take_number
LIMIT 100;
SELECT count() FROM slateiq.take WHERE day_number = 12 AND status = 'circled';
SELECT scene_number, shot, take_number, take_id, clip_uri, director_note, left(performance_note, 100) as perf_note
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.day_number = 12 AND t.status = 'circled'
ORDER BY toInt32OrZero(scene_number), scene_number, shot, take_number
LIMIT 100;
SELECT take_id, scene_number, shot, take_number, status, director_note
FROM slateiq.take
WHERE day_number = 12 AND scene_number = '6'
ORDER BY shot, take_number, camera
LIMIT 50;
SELECT planned_scenes FROM slateiq.shooting_day WHERE day_number = 12;
SELECT scene_number, shot, take_number, take_id, clip_uri, director_note, performance_note
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.day_number = 12 AND t.status = 'circled'
ORDER BY toInt32OrZero(scene_number), scene_number, shot, take_number
LIMIT 100;
SELECT * FROM slateiq.continuity_note LIMIT 10;
```

</details>

<details><summary>Answer</summary>

From the **38 circled takes** logged on **Day 12 (2026-09-04)**, here is the breakdown of what was printed and why, organized by scene. 

*Note on Multi-Cam Setups (Scenes 6, 39, 91):* When a multi-cam take is circled, all cameras rolling on that take are printed. This is why some secondary cameras carry technical notes (like dolly bumps, soft focus, or boom dips) while the primary camera holds the hero performance.

---

### **Scene 6 (INT. CORRIDOR - NIGHT)**
*Thom walks the quay alone; the city burns on the horizon.*
* **6/A/6 (Cam A)** | `TOS-D12-S6-A-06-A` | **Director:** "second unit will pick up the insert" | **Performance:** "Eyes stay in it right to the cut."
* **6/A/6 (Cam B)** | `TOS-D12-S6-A-06-B` | **Director:** "one more for safety" | **Performance:** "Grounded, quiet, holds the silence."
* **6/B/3 (Cam A)** | `TOS-D12-S6-B-03-A` | **Director:** "loved the stillness" | **Performance:** "Technically clean, performance flat."
* **6/B/3 (Cam B)** | `TOS-D12-S6-B-03-B` | **Director:** "one more for safety" | **Performance:** "Rushed the button line."
* **6/B/3 (Cam C)** | `TOS-D12-S6-B-03-C` | **Director:** "loved the stillness" | **Performance:** "Best emotional landing so far."
* **6/C/8 (Cam A)** | `TOS-D12-S6-C-08-A` | **Director:** "boom dipped, go again" | **Performance:** "Nice overlap with the off-camera cue."
* **6/C/8 (Cam B)** | `TOS-D12-S6-C-08-B` | **Director:** "camera bumped the dolly" | **Performance:** "Nice overlap with the off-camera cue."
* **6/D/1 (Cam A)** | `TOS-D12-S6-D-01-A` | **Director:** "one more for safety" | **Performance:** "Nice overlap with the off-camera cue."
* **6/D/1 (Cam B)** | `TOS-D12-S6-D-01-B` | **Director:** "less shouty" | **Performance:** "Eyes stay in it right to the cut."
* **6/E/2 (Cam A)** | `TOS-D12-S6-E-02-A` | **Director:** "too fast, let it breathe" | **Performance:** "Big swing — usable but broad."
* **6/E/2 (Cam B)** | `TOS-D12-S6-E-02-B` | **Director:** "camera bumped the dolly" | **Performance:** "Grounded, quiet, holds the silence."
* **6/F/3 (Cam A)** | `TOS-D12-S6-F-03-A` | **Director:** "boom dipped, go again" | **Performance:** "Eyes stay in it right to the cut."
* **6/F/5 (Cam A)** | `TOS-D12-S6-F-05-A` | **Director:** "boom dipped, go again" | **Performance:** "Best emotional landing so far."
* **6/G/2 (Cam A)** | `TOS-D12-S6-G-02-A` | **Director:** "loved the stillness" | **Performance:** "Best emotional landing so far."
* **6/G/2 (Cam B)** | `TOS-D12-S6-G-02-B` | **Director:** "she found it — that's the take" | **Performance:** "Grounded, quiet, holds the silence."

### **Scene 12 (EXT. BRIDGE - DAY)**
*Young man and woman with a robotic arm discuss their passions.*
* **12/A/1 (Cam A)** | `TOS-D12-S12-A-01-A` | **Director:** "Good energy, keep this one." | **Performance:** "Strong comedic timing and natural chemistry between the actors. The robotic arm prop is handled convincingly."
* **12/B/2 (Cam B)** | `TOS-D12-S12-B-02-B` | **Director:** "Cleaner. Print." | **Performance:** "The transition to the scope POV is clean, and the visual effects tracking of the flying vessel are highly detailed and well-integrated."

### **Scene 14A (EXT. BALCONY - DAY)**
*Older man wakes up on a covered balcony, rubbing his sore neck.*
* **14A/A/1 (Cam A)** | `TOS-D12-S14A-A-01-A` | **Director:** "Nice reset on the walk-in." | **Performance:** "Strong, understated performance showing physical weariness and defensive vulnerability."

### **Scene 27 (INT. MACHINE ROOM - DAY)**
*Injured older man lets go of a rope, clutches his shoulder, and walks toward a glowing machine.*
* **27/A/1 (Cam A)** | `TOS-D12-S27-A-01-A` | **Director:** "That's the one — the beat lands." | **Performance:** "Strong physical performance showing pain transitioning to determination."

### **Scene 33 (EXT. CANAL - DAY)**
*Man with a cybernetic eye piece encourages an older, white-haired man.*
* **33/A/1 (Cam A)** | `TOS-D12-S33-A-01-A` | **Director:** "Print it." | **Performance:** "Good energy and

…truncated…

</details>

---

### `ng_rate` — editor

**Q:** Which scene has the worst NG rate so far?

**Routing:** slateiq_coordinator → production_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly identified Scene 46 as having the worst NG rate of 38.4% (28/73 takes), provided the top 3 worst scenes with correct ratios, and listed plausible causes supported by the database queries.  
**Latency:** 37.7s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT 
    scene_number,
    count() AS total_takes,
    countIf(status = 'ng') AS ng_takes,
    round(countIf(status = 'ng') * 100.0 / count(), 1) AS ng_rate
FROM slateiq.take
GROUP BY scene_number
ORDER BY ng_rate DESC, total_takes DESC
LIMIT 10;
SELECT 
    s.scene_number,
    s.slug,
    s.page_eighths,
    count(t.take_id) AS total_takes,
    countIf(t.status = 'ng') AS ng_takes,
    round(countIf(t.status = 'ng') * 100.0 / count(t.take_id), 1) AS ng_rate
FROM slateiq.scene s
JOIN slateiq.take t ON s.scene_number = t.scene_number
GROUP BY s.scene_number, s.slug, s.page_eighths
ORDER BY ng_rate DESC, total_takes DESC
LIMIT 5;
SELECT 
    t.take_id,
    t.shot,
    t.take_number,
    t.director_note,
    groupArray(e.flag_type) AS flags
FROM slateiq.take t
LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.kind = 'flag'
WHERE t.scene_number = '46' AND t.status = 'ng'
GROUP BY t.take_id, t.shot, t.take_number, t.director_note
LIMIT 10;
SELECT 
    take_id,
    shot,
    take_number,
    camera,
    status,
    director_note
FROM slateiq.take
WHERE scene_number = '46' AND shot = 'F' AND take_number = 4
LIMIT 10;
SELECT 
    status,
    count() AS count
FROM slateiq.take
WHERE scene_number = '46'
GROUP BY status
ORDER BY count DESC;
SELECT 
    status,
    count() AS count
FROM slateiq.take
WHERE scene_number = '112'
GROUP BY status
ORDER BY count DESC;
SELECT 
    t.scene_number,
    e.flag_type,
    count() AS flag_count,
    round(avg(e.severity), 1) AS avg_severity
FROM slateiq.take t
JOIN slateiq.take_event e ON t.take_id = e.take_id
WHERE t.scene_number IN ('46', '112') AND t.status = 'ng' AND e.kind = 'flag' AND e.flag_type != ''
GROUP BY t.scene_number, e.flag_type
ORDER BY t.scene_number, flag_count DESC;
SELECT 
    t.take_id,
    t.shot,
    t.take_number,
    t.camera,
    t.director_note
FROM slateiq.take t
WHERE t.scene_number = '46' AND t.status = 'ng' AND t.director_note != ''
LIMIT 10;
SELECT 
    take_id,
    shot,
    take_number,
    camera,
    status,
    director_note
FROM slateiq.take
WHERE scene_number = '46' AND shot = 'A' AND take_number = 4
LIMIT 10;
SELECT 
    take_id,
    shot,
    take_number,
    camera,
    status,
    director_note
FROM slateiq.take
WHERE scene_number = '46' AND shot = 'A'
ORDER BY take_number, camera
LIMIT 20;
```

</details>

<details><summary>Answer</summary>

**Scene 46 (INT. CONTROL ROOM - DAY) has the worst NG rate so far, with 38.4% of its takes flagged as No Good.**

Out of **73 total takes** logged for this 1 4/8-page scene, **28 were marked NG**, while 26 were held, 16 were circled, and 3 were wild. 

The high NG rate was driven by a mix of technical resets and performance adjustments:
* **Camera & Focus Issues:** Focus pulls missed on physical movements, such as on 46/C/5 (`TOS-D07-S46-C-05-A`) where the director noted *"focus soft on the turn"*.
* **Sound & Boom Interference:** Multiple takes were killed by boom dips, including 46/C/3 (`TOS-D07-S46-C-03-A`) and 46/E/1 (`TOS-D07-S46-E-01-B`) with notes to *"boom dipped, go again"*.
* **Art Department Resets:** Take 46/B/4 (`TOS-D07-S46-B-04-A`) was cut to *"reset props, hero glass moved"*.

Interestingly, some takes marked NG actually captured the performance sweet spot before a technical issue cut them short. For example, on 46/A/4 (`TOS-D07-S46-A-04-A`), the director noted *"she found it — that's the take"*, but the slate was ultimately marked NG (likely due to a technical issue on the B-camera or a late-stage safety reset).

### Top 3 Worst Scenes by NG Rate (Min. 10 Takes)
1. **Scene 46 (INT. CONTROL ROOM - DAY):** **38.4% NG** (28 NG / 73 takes) — 1 4/8 pages.
2. **Scene 112 (INT. SAFEHOUSE - DAY):** **35.6% NG** (16 NG / 45 takes) — 2 pages.
3. **Scene 100 (EXT. BRIDGE - DAWN):** **33.3% NG** (11 NG / 33 takes) — 1 2/8 pages.

*SQL: Queried the `slateiq.take` and `slateiq.scene` tables to calculate the percentage of NG takes grouped by scene_number, filtering for overall volume and analyzing director notes for the worst-performing setups.*

```json
{
  "takes": [
    {
      "take_id": "TOS-D07-S46-A-04-A",
      "clip_uri": "",
      "t": 0,
      "label": "46/A/4 (A Cam)",
      "reason": "Marked NG despite note: 'she found it — that's the take'"
    },
    {
      "take_id": "TOS-D07-S46-C-03-A",
      "clip_uri": "",
      "t": 0,
      "label": "46/C/3 (A Cam)",
      "reason": "NG due to 'boom dipped, go again'"
    },
    {
      "take_id": "TOS-D07-S46-C-05-A",
      "clip_uri": "",
      "t": 0,
      "label": "46/C/5 (A Cam)",
      "reason": "NG due to 'focus soft on the turn'"
    }
  ],
  "sql": [
    "SELECT scene_number, count() AS total_takes, countIf(status = 'ng') AS ng_takes, round(countIf(status = 'ng') * 100.0 / count(), 1) AS ng_rate FROM slateiq.take GROUP BY scene_number ORDER BY ng_rate DESC, total_takes DESC LIMIT 10",
    "SELECT s.scene_number, s.slug, s.page_eighths, count(t.take_id) AS total_takes, countIf(t.status = 'ng') AS ng_takes, round(countIf(t.status = 'ng') * 100.0 / count(t.take_id), 1) AS ng_rate FROM slateiq.scene s JOIN slateiq.take t ON s.scene_number = t.scene_number GROUP BY s.scene_number, s.slug, s.page_eighths ORDER BY ng_rate DESC, total_takes DESC LIMIT 5",
    "SELECT status, count() AS count FROM slateiq.take WHERE scene_number = '46' GROUP BY status ORDER BY count DESC"
  ]
}
```

</details>

---

### `on_schedule` — ad

**Q:** Are we on schedule? Pages planned versus pages actually shot.

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly satisfies the rubric by comparing planned to shot pages, stating we are 3 4/8 pages behind, and specifying we are on Day 12 of a 30-day schedule.  
**Latency:** 21.6s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT sum(pages_shot_eighths) / 8.0                       AS shot_pages,
       sum(pages_planned_eighths) / 8.0                    AS planned_pages,
       count()                                             AS days_shot,
       (SELECT sum(page_eighths) / 8.0 FROM slateiq.scene
        WHERE scene_number NOT IN
              (SELECT DISTINCT scene_number FROM slateiq.take)) AS remaining_pages
FROM slateiq.daily_progress WHERE day_number <= 12;
SELECT day_number, 
       pages_planned_eighths / 8.0 AS planned, 
       pages_shot_eighths / 8.0 AS shot,
       sum(pages_shot_eighths / 8.0) OVER (ORDER BY day_number) AS cume_shot,
       sum(pages_planned_eighths / 8.0) OVER (ORDER BY day_number) AS cume_planned
FROM slateiq.daily_progress 
WHERE day_number <= 12 
ORDER BY day_number;
SELECT day_number, weather, notes FROM slateiq.shooting_day WHERE day_number IN (8, 11);
```

</details>

<details><summary>Answer</summary>

**3 4/8 pages behind after Day 12 -- but at the current pace we still finish with about 1 1/2 days of cushion.**

Here is the production health breakdown as of Day 12 of our 30-day schedule:

### Schedule & Page Progress
* **Cumulative Planned:** 52 pages
* **Cumulative Shot:** 48 4/8 pages (93.3% of plan)
* **Current Deficit:** 3 4/8 pages behind (representing about 7/8 of a shooting day at our current pace)

The entire deficit is explained by two specific weather events. On **Day 8** and **Day 11**, we hit persistent drizzle and low clouds, resulting in weather holds that cost us setups. We shot only 2 pages (of 3 6/8 planned) on Day 8, and 3 pages (of 4 6/8 planned) on Day 11, carrying the remaining scenes forward. Outside of those two rainouts, the crew has hit the daily page targets exactly.

### Forecast & Cushion
* **Remaining Pages to Shoot:** 66 7/8 pages (scenes with no takes logged yet)
* **Current Shooting Pace:** 4.04 pages per day (48 4/8 pages shot over 12 days)
* **Estimated Days Needed:** 16.5 days (66 7/8 pages remaining / 4.04 pace)
* **Scheduled Days Remaining:** 18 days (Days 13 to 30)
* **Projected Cushion:** **About 1 1/2 days of cushion**

**The Verdict:** We are not going over schedule. While we are currently 3 4/8 pages behind our original day-by-day plan, our overall shooting pace is healthy enough that we are projected to wrap the remaining pages with a 1 1/2-day buffer before our 30-day limit. This forecast assumes our current pace holds and we do not suffer any further rainouts or major disruptions.

SQL: Queried cumulative planned vs. shot pages from `slateiq.daily_progress` to date, checked weather notes for Days 8 and 11, and calculated remaining pages from `slateiq.scene` where no takes exist.

</details>

---

### `print_ratio` — producer

**Q:** What's our print ratio by scene? Where are we burning the most film?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly calculated and ranked the print ratios, correctly defined the terms, highlighted the worst offenders with a judgment, and all numbers match the database output.  
**Latency:** 26.1s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT scene_number, slug, takes, circled, print_ratio 
FROM slateiq.scene_progress 
WHERE takes > 0 
ORDER BY print_ratio DESC 
LIMIT 15;
SELECT 
    t.scene_number,
    s.slug,
    count() AS total_takes,
    countIf(t.status = 'circled') AS circled_takes,
    round(count() / greatest(countIf(t.status = 'circled'), 1), 2) AS print_ratio,
    round(sum(t.duration_s) / greatest(sumIf(t.duration_s, t.status = 'circled'), 1), 1) AS shooting_ratio,
    round(sum(t.duration_s) / 60.0, 1) AS total_camera_minutes
FROM slateiq.take t
JOIN slateiq.scene s USING scene_number
GROUP BY t.scene_number, s.slug
ORDER BY print_ratio DESC
LIMIT 15;
SELECT scene_number, slug, takes, circled, print_ratio 
FROM slateiq.scene_progress 
WHERE circled = 0 AND takes > 0
LIMIT 10;
SELECT sum(takes) AS total_takes, sum(camera_minutes) AS total_minutes FROM slateiq.daily_progress WHERE day_number <= 12;
```

</details>

<details><summary>Answer</summary>

Based on 2,503 takes and 2,050.5 camera minutes logged across Days 1–12, **Scene 98 (INT. WORKSHOP - DUSK) is our most inefficient scene, leading both in print ratio (7.6:1) and duration-based shooting ratio (10.1:1), while Scene 99 (INT. SAFEHOUSE - NIGHT) has burned the most absolute film with 98.5 camera minutes across 123 takes.**

To keep our terms straight:
*   **Print Ratio** (takes per circled take) measures setup efficiency (total takes / circled takes).
*   **Shooting Ratio** measures actual film burned (total camera duration / circled camera duration).

Here is where we are burning the most film across both metrics:

### Top 5 Scenes by Print Ratio (Takes per Circled Take)
These are the scenes where we are running the most takes to get our circled prints:
1.  **Scene 98 (INT. WORKSHOP - DUSK)**: **7.6:1** (83 takes, 11 circled) | *Shooting Ratio: 10.1:1* | *Total: 62.3 camera mins*
2.  **Scene 19 (INT. BAR - NIGHT)**: **7.2:1** (79 takes, 11 circled) | *Shooting Ratio: 5.9:1* | *Total: 60.8 camera mins*
3.  **Scene 91 (INT. CONTROL ROOM - NIGHT)**: **6.7:1** (47 takes, 7 circled) | *Shooting Ratio: 6.4:1* | *Total: 33.9 camera mins*
4.  **Scene 13 (EXT. ALLEY - NIGHT)**: **6.6:1** (46 takes, 7 circled) | *Shooting Ratio: 8.0:1* | *Total: 35.1 camera mins*
5.  **Scene 112 (INT. SAFEHOUSE - DAY)**: **6.4:1** (45 takes, 7 circled) | *Shooting Ratio: 7.4:1* | *Total: 33.0 camera mins*

### Top 3 Scenes by Absolute Volume (Most Film Burned)
Even with more reasonable print ratios, these heavy scenes consumed the most actual rolling time on set:
1.  **Scene 99 (INT. SAFEHOUSE - NIGHT)**: **98.5 camera minutes** across **123 takes** (Print Ratio: 5.4:1 | Shooting Ratio: 5.5:1)
2.  **Scene 55 (EXT. CITY SQUARE - DUSK)**: **85.9 camera minutes** across **99 takes** (Print Ratio: 5.8:1 | Shooting Ratio: 6.2:1)
3.  **Scene 48 (INT. WORKSHOP - DAY)**: **74.0 camera minutes** across **93 takes** (Print Ratio: 5.2:1 | Shooting Ratio: 5.1:1)

**The Verdict:** 
Keep an eye on the **Workshop (Scene 98)** and **Alley (Scene 13)** setups. A 10:1 shooting ratio on Scene 98 means we are discarding 90% of the footage we roll, which is a massive drain on the camera department and DIT. 

SQL: Queried `slateiq.scene_progress` and joined `slateiq.take` with `slateiq.scene` to calculate print ratios, duration-based shooting ratios, and total camera minutes grouped by scene.

</details>

---

### `scenes_at_risk` — ad

**Q:** Which scenes are at risk of not being finished?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly answers the question using SQL queries that target unshot scenes, high-severity continuity conflicts, and high NG rates, presenting the findings with detailed evidence and correct structured output.  
**Latency:** 46.9s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT d.day_number, psc AS scene_number, s.page_eighths/8.0 AS pages, s.slug
FROM slateiq.shooting_day d
ARRAY JOIN d.planned_scenes AS psc
JOIN slateiq.scene s ON s.scene_number = psc
WHERE d.day_number <= 12 AND psc NOT IN (SELECT DISTINCT scene_number FROM slateiq.take)
ORDER BY d.day_number, scene_number
LIMIT 100;
SELECT scene_number, slug, takes, circled, print_ratio, status
FROM slateiq.scene_progress
WHERE status IN ('no_circled', 'partial') OR (takes > 0 AND circled = 0)
ORDER BY takes DESC
LIMIT 100;
SELECT scene_number, category, severity, description
FROM slateiq.continuity_note
WHERE severity >= 4
ORDER BY severity DESC
LIMIT 100;
SELECT scene_number,
       count() AS total_takes,
       countIf(status = 'ng') AS ng_takes,
       round(countIf(status = 'ng') / count(), 2) AS ng_rate
FROM slateiq.take
GROUP BY scene_number
HAVING total_takes > 5 AND ng_rate > 0.3
ORDER BY ng_rate DESC
LIMIT 20;
SELECT scene_number, slug, takes, circled, print_ratio
FROM slateiq.scene_progress
WHERE print_ratio > 8.0 AND takes > 0
ORDER BY print_ratio DESC
LIMIT 20;
SELECT scene_number, slug, takes, circled, print_ratio
FROM slateiq.scene_progress
WHERE takes > 0
ORDER BY print_ratio DESC
LIMIT 10;
SELECT sum(pages_shot_eighths) / 8.0                       AS shot_pages,
       sum(pages_planned_eighths) / 8.0                    AS planned_pages,
       count()                                             AS days_shot,
       (SELECT sum(page_eighths) / 8.0 FROM slateiq.scene
        WHERE scene_number NOT IN
              (SELECT DISTINCT scene_number FROM slateiq.take)) AS remaining_pages
FROM slateiq.daily_progress WHERE day_number <= 12;
SELECT take_id, scene_number, shot, take_number, clip_uri, status
FROM slateiq.take
WHERE scene_number IN ('12', '13', '27', '33') AND status = 'circled'
LIMIT 10;
SELECT take_id, clip_uri FROM slateiq.take WHERE take_id IN ('TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B', 'TOS-D11-S13-C-02-B', 'TOS-D11-S13-B-02-C');
SELECT count() FROM slateiq.take WHERE day_number = 12;
```

</details>

<details><summary>Answer</summary>

**3 4/8 pages behind after Day 12 -- but at the current pace we still finish with about 1 1/2 days of cushion.**

While our overall schedule health remains stable due to a solid shooting pace (averaging 4.04 pages per day against 66 7/8 remaining pages), we have several specific scenes at risk due to weather rain-outs, severe continuity conflicts, or high NG rates.

### 1. Unshot Scenes (Rain-Outs)
We have **4 scenes (totaling 3 4/8 pages)** that were scheduled on Days 8 and 11 but were completely missed due to rain. These must be rescheduled:
*   **Scene 31** (INT. WORKSHOP - DAY, 0.5 pages) — Day 8 rain-out.
*   **Scene 70** (INT. LAB - DAY, 1.25 pages) — Day 8 rain-out.
*   **Scene 74** (INT. CORRIDOR - NIGHT, 0.5 pages) — Day 11 rain-out.
*   **Scene 96** (INT. BAR - NIGHT, 1.25 pages) — Day 11 rain-out.

### 2. Scenes at Risk from Severe Continuity Conflicts (Severity 5)
These scenes have major continuity discrepancies between takes that will cause serious headaches in the edit suite or require expensive VFX fixes/reshoots:
*   **Scene 12** (INT. SAFEHOUSE - DAY): Severe set dressing conflict. In take `12/B/1-B`, the foreground character is sleeping under a newspaper on a balcony, but in take `12/B/2-B`, the set is dressed with a cot.
*   **Scene 13** (EXT. ALLEY - NIGHT): Lighting mismatch. The practical light is on in take `13/C/2-B` but off in take `13/B/2-C` (the grade cannot match). This scene also suffered a high **33% NG rate** (15 of 46 takes).
*   **Scene 27** (EXT. BRIDGE - DAY): Major action match conflict. In Take A, the older man is clutching an injured shoulder and letting go of a rope, but in Take B he enters uninjured and is accompanied by a young woman who is completely absent in Take A.
*   **Scene 33** (EXT. BRIDGE - NIGHT): Multiple severe conflicts across dialogue, props, and action matches (e.g., the cybernetic man handles a microphone and radio antenna in Take A, which are completely missing in Take B).
*   **Scene 19** (INT. BAR - NIGHT) & **Scene 23** (INT. MED BAY - NIGHT): Severe set dressing conflicts where chairs were moved 40cm between setups. Scene 19 also burned a lot of film with a high **7.18:1 print ratio** (79 takes / 11 circled).
*   **Scenes 14, 48, 88A, and 98**: Severe hair/makeup conflicts with blood on the left temple in some setups and the right temple in others. Scene 98 also has our highest print ratio at **7.55:1** (83 takes / 11 circled).

### 3. Scenes at Risk from High NG Rates
These scenes are taking an excessive number of setups and takes to get right, indicating performance or technical friction on set:
*   **Scene 46** (INT. CONTROL ROOM - NIGHT): **38% NG rate** (28 of 73 takes).
*   **Scene 112** (INT. SAFEHOUSE - DAY): **36% NG rate** (16 of 45 takes).
*   **Scene 100** (INT. SAFEHOUSE - DAY): **33% NG rate** (11 of 33 takes).
*   **Scene 91** (INT. CONTROL ROOM - NIGHT): **32% NG rate** (15 of 47 takes).

SQL: Queried unshot planned scenes, continuity notes with severity >= 4, high NG rates, and cumulative page progress to date.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-B-01-B",
      "clip_uri": "clips/TOS-D12-S12-B-01-B.mp4",
      "t": 0.0,
      "label": "12/B/1-B",
      "reason": "Set dressing conflict: character sleeping under newspaper on balcony"
    },
    {
      "take_id": "TOS-D12-S12-B-02-B",
      "clip_uri": "clips/TOS-D12-S12-B-02-B.mp4",
      "t": 0.0,
      "label": "12/B/2-B",
      "reason": "Set dressing conflict: character resting on a cot"
    },
    {
      "take_id": "TOS-D11-S13-C-02-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d11/TOS-D11-S13-C-02-B.mp4",
      "t": 0.0,
      "label": "13/C/2-B",
      "reason": "Lighting conflict: practical light is ON"
    },
    {
      "take_id": "TOS-D11-S13-B-02-C",
      "clip_uri": "gs://slateiq-dailies/tos2026/d11/TOS-D11-S13-B-02-C.mp4",
      "t": 0.0,
      "label": "13/B/2-C",
      "reason": "Lighting conflict: practical light is OFF"
    }
  ],
  "sql": [
    "SEL

…truncated…

</details>

---

### `overtime_trend` — producer

**Q:** How is our wrap time trending? Are we going into overtime?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 5/5 — The assistant correctly used call_time and wrap_time to calculate day lengths, analyzed the trend, flagged days over 12 hours, and all presented figures mathematically align with the database results.  
**Latency:** 22.8s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT day_number, shoot_date, call_time, planned_wrap, actual_wrap, wrap_delay_min
FROM slateiq.shooting_day
LEFT JOIN slateiq.daily_progress USING (day_number)
WHERE day_number <= 12
ORDER BY day_number ASC
LIMIT 30;
SELECT
    day_number,
    shoot_date,
    dateDiff('minute', call_time, actual_wrap) AS actual_duration_min,
    wrap_delay_min
FROM slateiq.shooting_day
LEFT JOIN slateiq.daily_progress USING (day_number)
WHERE day_number <= 12
ORDER BY day_number ASC
LIMIT 30;
SELECT
    sumIf(wrap_delay_min, wrap_delay_min > 0) AS total_overtime_min,
    countIf(wrap_delay_min > 0) AS overtime_days,
    avg(wrap_delay_min) AS avg_delay_min
FROM slateiq.daily_progress
WHERE day_number <= 12;
```

</details>

<details><summary>Answer</summary>

Our wrap times are trending remarkably stable on normal days, but weather disruptions on Days 8 and 11 have pushed us into a cumulative **6 hours and 35 minutes of overtime** across the first 12 days of production.

Here is how our wrap times and day lengths break down across the 12 days shot so far:

### The Overtime Breakdown
Out of 12 shooting days, we have gone into overtime on 6 days, totaling **395 minutes (6h 35m)**:
*   **Day 3 (Aug 24):** 12h 35m day length (+35m wrap delay)
*   **Day 5 (Aug 26):** 12h 15m day length (+15m wrap delay)
*   **Day 7 (Aug 28):** 12h 35m day length (+35m wrap delay)
*   **Day 8 (Aug 31):** **14h 18m day length (+2h 18m wrap delay)** — *Rain day*
*   **Day 11 (Sep 3):** **14h 37m day length (+2h 37m wrap delay)** — *Rain day*
*   **Day 12 (Sep 4 - Today):** 12h 15m day length (+15m wrap delay)

### The Trend Analysis
*   **Highly Efficient Baseline:** On normal shooting days, our camera and rigging crews are incredibly disciplined. Days 1, 2, 4, 6, and 9 wrapped exactly on their 12-hour scheduled mark. Day 10 even wrapped 10 minutes early (11h 50m day length). 
*   **Weather Vulnerability:** The major overtime spikes are entirely weather-driven. Days 8 and 11 lost critical setups to rain, forcing the crew to wait out the downpours and scramble to make our pages, resulting in grueling 14+ hour days.
*   **Today's Recovery:** Today (Day 12) shows we have stabilized after yesterday's rain-soaked marathon. We wrapped at 17:15 against a planned 17:00 wrap, keeping overtime to a negligible 15 minutes.

We are not in a chronic, structural overtime trend. As long as the weather cooperates, the crew is wrapping on time or within a 15-to-35-minute window.

SQL: Queried `slateiq.shooting_day` and `slateiq.daily_progress` to calculate actual day durations, wrap delays, and cumulative overtime statistics for Days 1 through 12.

</details>

---

### `forecast` — producer

**Q:** At the current pace, how many more shooting days do we need?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query  
**Judge:** 5/5 — The agent accurately calculates the pages per day achieved (4.04), pages remaining (66 7/8), and correctly projects the days needed (16.5) versus remaining (18), while explicitly stating its assumptions.  
**Latency:** 26.5s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT sum(pages_shot_eighths) / 8.0                       AS shot_pages,
       sum(pages_planned_eighths) / 8.0                    AS planned_pages,
       count()                                             AS days_shot,
       (SELECT sum(page_eighths) / 8.0 FROM slateiq.scene
        WHERE scene_number NOT IN
              (SELECT DISTINCT scene_number FROM slateiq.take)) AS remaining_pages
FROM slateiq.daily_progress WHERE day_number <= 12;
SELECT day_number, pages_planned_eighths/8.0 AS planned, pages_shot_eighths/8.0 AS shot, weather, notes
FROM slateiq.shooting_day JOIN slateiq.daily_progress USING (day_number)
WHERE day_number IN (8, 11);
```

</details>

<details><summary>Answer</summary>

**3 4/8 pages behind after Day 12 -- but at the current pace we still finish with about 1 1/2 days of cushion.**

Here is the breakdown of where we stand based on the daily progress and scene records through Day 12:

* **The Deficit:** We have shot **48 4/8 pages** against a planned **52 pages**, putting us **3 4/8 pages behind** schedule (about 7/8 of a shooting day at our current pace). This deficit is entirely explained by weather holds on Day 8 and Day 11, where persistent drizzle forced us to lose setups and carry scenes over, costing us exactly 1 6/8 pages on each of those days.
* **Current Pace:** Over our first 12 shooting days, we are averaging **4.04 pages per day**.
* **Remaining Work:** We have **66 7/8 pages** of scenes left to shoot that currently have no takes.
* **The Forecast:** At our current pace, we need **16.5 shooting days** to complete the remaining pages. Since we have **18 days left** on our 30-day calendar, we are projected to finish with **1.45 days of cushion** (about 1 1/2 days under schedule).

This forecast assumes our current pace holds and we don't run into any further weather delays or rainouts.

SQL: Queried cumulative pages planned vs. shot, remaining unshot scene pages, and weather notes for Days 8 and 11 from the daily progress and shooting day tables.

</details>

---

### `setups_per_day` — ad

**Q:** How many setups did we get on day 12 and how does that compare to our average?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 4/5 — The agent correctly answered the question with grounded data, but did not use the `uniqExact(shot)` function as specified in the rubric, opting instead to query a pre-calculated `setups` column from the daily progress table.  
**Latency:** 17.4s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT 
    (SELECT setups FROM slateiq.daily_progress WHERE day_number = 12) AS day_12_setups,
    avg(setups) AS avg_setups,
    count() AS days_shot
FROM slateiq.daily_progress 
WHERE day_number <= 12 AND setups > 0;
SELECT 
    avg(setups) AS avg_prior_setups
FROM slateiq.daily_progress 
WHERE day_number < 12 AND setups > 0;
SELECT day_number, setups, pages_shot_eighths / 8.0 AS pages_shot
FROM slateiq.daily_progress 
WHERE day_number <= 12 
ORDER BY day_number ASC;
```

</details>

<details><summary>Answer</summary>

We crushed our setup count on Day 12, matching our production high of **31 setups**—which is **45% above our historical average** of 21.4 setups per day. 

Here is how Day 12 compares to the rest of the shoot:

*   **The Benchmark:** Day 12 tied Day 7 (31 setups) for our most active day of the production so far. 
*   **Historical Average (Days 1–11):** 21.4 setups per day.
*   **Overall Average (Days 1–12):** 22.2 setups per day.
*   **The Rain Factor:** Our historical average is heavily skewed by Days 8 and 11, where we lost setups to rain (logging only 8 setups on each of those days). If we exclude those two weather-impacted days, our running average is **24.3 setups per day**. Even against this clean baseline, Day 12's 31 setups represents a **27.5% increase in efficiency**.

This high setup count on Day 12 translated directly to pages in the can: we knocked out a massive **9 3/8 pages** (9.375 pages), our highest single-day page count of the entire shoot.

### Daily Setup & Page Trend (Days 1–12)
*   **Day 1:** 27 setups (2.5 pages)
*   **Day 2:** 24 setups (4.125 pages)
*   **Day 3:** 25 setups (2.25 pages)
*   **Day 4:** 24 setups (1.625 pages)
*   **Day 5:** 25 setups (5.5 pages)
*   **Day 6:** 19 setups (7.25 pages)
*   **Day 7:** 31 setups (4.5 pages)
*   **Day 8:** 8 setups (2.0 pages) *— Rain day*
*   **Day 9:** 25 setups (3.375 pages)
*   **Day 10:** 19 setups (3.0 pages)
*   **Day 11:** 8 setups (3.0 pages) *— Rain day*
*   **Day 12 (Today):** 31 setups (9.375 pages)

```json
{
  "sql": [
    "SELECT (SELECT setups FROM slateiq.daily_progress WHERE day_number = 12) AS day_12_setups, avg(setups) AS avg_setups, count() AS days_shot FROM slateiq.daily_progress WHERE day_number <= 12 AND setups > 0",
    "SELECT avg(setups) AS avg_prior_setups FROM slateiq.daily_progress WHERE day_number < 12 AND setups > 0",
    "SELECT day_number, setups, pages_shot_eighths / 8.0 AS pages_shot FROM slateiq.daily_progress WHERE day_number <= 12 ORDER BY day_number ASC"
  ]
}
```

</details>

---

### `continuity_scene` — script_supervisor

**Q:** Are there any continuity problems in scene 12? Which takes conflict?

**Routing:** slateiq_coordinator → continuity_agent (expected `continuity_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly identified the continuity conflicts and conflicting takes in Scene 12 using the SQL query results, providing a highly accurate, grounded, and industry-appropriate response.  
**Latency:** 23.8s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT take_id_a, take_id_b, category, severity, description 
FROM slateiq.continuity_note 
WHERE scene_number = '12' 
ORDER BY severity DESC 
LIMIT 100;
SELECT e.speaker,
       e.text,
       count() AS times,
       groupArray(10)(t.shot) AS shots,
       any(e.t_offset_s) AS first_offset,
       any(e.take_id) AS example_take
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '12' AND e.kind = 'dialogue'
GROUP BY e.speaker, e.text
ORDER BY e.speaker, times DESC
LIMIT 100;
SELECT take_id, clip_uri, status, take_number, shot 
FROM slateiq.take 
WHERE take_id IN ('TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B') 
LIMIT 10;
SELECT count() FROM slateiq.take WHERE scene_number = '12';
SELECT take_id, shot, take_number, status FROM slateiq.take WHERE scene_number = '12' LIMIT 10;
```

</details>

<details><summary>Answer</summary>

Yes, we have two continuity conflicts in **Scene 12**, specifically between **Take 1** and **Take 2** of setup **B** (the B-camera angle). 

From the 4 takes logged for Scene 12, here are the details of the conflicts:

### 1. Set Dressing — Severity 5 (Critical)
* **The Conflict:** In **Take 1** (`12/B/1`), the foreground character is sleeping under a newspaper on a balcony. In **Take 2** (`12/B/2`), the set is dressed with a cot where the character is resting.
* **Impact:** This is a major set dressing change that will completely break the cut if you try to intercut these two takes. 

### 2. Props — Severity 3 (Moderate)
* **The Conflict:** In **Take 1** (`12/B/1`), the sniper loads a red cartridge into his rifle. In **Take 2** (`12/B/2`), this action is absent, and the soldier only aims the weapon.

### Dialogue & Script Match
Our dialogue analysis shows **no line variations** across the takes for Scene 12. The readings of the lines between Celia and the Man are perfectly consistent.

### Recommendation
Since **Take 2** (`TOS-D12-S12-B-02-B`) is the **circled take** and Take 1 is currently on **hold**, the editor should cut around Take 1 entirely. Do not attempt to use any of Take 1's B-roll or action beats, as the newspaper-to-cot transition and the rifle loading action will cause jarring continuity breaks.

SQL: Queried `slateiq.continuity_note` for Scene 12 conflicts and aggregated `slateiq.take_event` dialogue lines to check for script variations.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-B-01-B",
      "clip_uri": "clips/TOS-D12-S12-B-01-B.mp4",
      "t": 0.0,
      "label": "12/B/1 (Hold)",
      "reason": "Character under newspaper; sniper loads red cartridge"
    },
    {
      "take_id": "TOS-D12-S12-B-02-B",
      "clip_uri": "clips/TOS-D12-S12-B-02-B.mp4",
      "t": 0.0,
      "label": "12/B/2 (Circled)",
      "reason": "Character on cot; sniper only aims rifle"
    }
  ],
  "sql": [
    "SELECT take_id_a, take_id_b, category, severity, description FROM slateiq.continuity_note WHERE scene_number = '12' ORDER BY severity DESC LIMIT 100",
    "SELECT e.speaker, e.text, count() AS times, groupArray(10)(t.shot) AS shots, any(e.t_offset_s) AS first_offset, any(e.take_id) AS example_take FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE t.scene_number = '12' AND e.kind = 'dialogue' GROUP BY e.speaker, e.text ORDER BY e.speaker, times DESC LIMIT 100"
  ]
}
```

</details>

---

### `line_variations` — script_supervisor

**Q:** Did the dialogue change between takes in scene 6? Show me the line variations.

**Routing:** slateiq_coordinator → continuity_agent (expected `continuity_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly analyzed that there were no dialogue variations in scene 6, and successfully presented the standard lines along with their frequencies, take slates, and offsets as requested.  
**Latency:** 197.3s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT e.speaker,
       e.text,
       count() AS times,
       groupArray(10)(t.shot) AS shots,
       any(e.t_offset_s) AS first_offset,
       any(e.take_id) AS example_take
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '6' AND e.kind = 'dialogue'
GROUP BY e.speaker, e.text
ORDER BY e.speaker, times DESC
LIMIT 100;
SELECT take_id, clip_uri, status, take_number, shot
FROM slateiq.take
WHERE take_id IN ('TOS-D12-S6-A-01-A', 'TOS-D12-S6-A-01-B', 'TOS-D12-S6-A-02-A');
SELECT count(), countIf(status='circled') FROM slateiq.take WHERE scene_number = '6';
```

</details>

<details><summary>Answer</summary>

Based on the dialogue events logged for **Scene 6** (from 66 takes shot), there are **no line variations** across the takes. 

Thom is the only speaker with dialogue in this scene, and he delivers his lines with perfect consistency. The scripted readings and their frequencies across all camera slates are:

1. **"Then we do it the hard way."** — Delivered 78 times (e.g., on take `6/A/1` at 3.0s).
2. **"I'm not leaving her down there."** — Delivered 78 times (e.g., on take `6/A/1` at 16.4s).
3. **"It was never about the machine."** — Delivered 76 times (e.g., on take `6/A/1` at 10.4s).
4. **"I can't do this again."** — Delivered 67 times (e.g., on take `6/A/2` at 3.0s).
5. **"Give me thirty seconds and stay off the comms."** — Delivered 62 times (e.g., on take `6/A/1` at 36.8s).
6. **"You were right. I hate that you were right."** — Delivered 59 times (e.g., on take `6/A/1` at 10.9s).

Since there are no rare or alternate readings for any of these lines, the dialogue remained completely uniform throughout the setups.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S6-A-01-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-A-01-A.mp4",
      "t": 3.0,
      "label": "6/A/1 (Hold)",
      "reason": "Scripted reading of 'Then we do it the hard way.'"
    },
    {
      "take_id": "TOS-D12-S6-A-02-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-A-02-A.mp4",
      "t": 3.0,
      "label": "6/A/2 (Hold)",
      "reason": "Scripted reading of 'I can't do this again.'"
    }
  ],
  "sql": [
    "SELECT e.speaker, e.text, count() AS times, groupArray(10)(t.shot) AS shots, any(e.t_offset_s) AS first_offset, any(e.take_id) AS example_take FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE t.scene_number = '6' AND e.kind = 'dialogue' GROUP BY e.speaker, e.text ORDER BY e.speaker, times DESC LIMIT 100",
    "SELECT take_id, clip_uri, status, take_number, shot FROM slateiq.take WHERE take_id IN ('TOS-D12-S6-A-01-A', 'TOS-D12-S6-A-01-B', 'TOS-D12-S6-A-02-A')"
  ]
}
```

**SQL:** Queried `slateiq.take_event` grouped by speaker and text for scene 6 to identify any low-frequency dialogue variations, then retrieved clip URIs for the representative takes.

</details>

---

### `emotional_intensity` — director

**Q:** Show me the three takes with the most emotionally intense delivery in scene 6.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 5/5 — The agent provided all the requested information (three takes, speaker, offset, and clip links) correctly, and the numbers are fully grounded according to the SQL results and the rubric guidance.  
**Latency:** 24.2s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.clip_uri, t.director_note,
       a.emotion_intensity, a.performance_note, a.quality_score
FROM slateiq.take t
JOIN slateiq.take_analysis a USING (take_id)
WHERE t.scene_number = '6'
ORDER BY a.emotion_intensity DESC
LIMIT 10;
SELECT take_id, event_id, t_offset_s, t_end_s, speaker, text, score, meta
FROM slateiq.take_event
WHERE take_id IN ('TOS-D12-S6-E-01-B', 'TOS-D12-S6-E-01-A', 'TOS-D12-S6-A-05-A', 'TOS-D12-S6-F-01-A')
  AND kind = 'emotion'
ORDER BY score DESC
LIMIT 50;
SELECT count() FROM slateiq.take WHERE scene_number = '6';
```

</details>

<details><summary>Answer</summary>

Based on 66 takes logged for scene 6, here are the takes with the most emotionally intense deliveries:

### 1. **6/E/1-B** (Camera B) — Intensity: **0.97**
* **Status**: Hold
* **Director's Note**: *"she found it — that's the take"*
* **Performance Note**: *"Big swing — usable but broad."*
* **Peak Moment**: Thom hits peak emotional intensity at **41.8s** (score: 0.67).
* **Clip**: `gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-E-01-B.mp4`

### 2. **6/E/1-A** (Camera A) — Intensity: **0.92**
* **Status**: Hold
* **Director's Note**: *"focus soft on the turn"*
* **Performance Note**: *"Technically clean, performance flat."*
* **Peak Moment**: Thom hits peak emotional intensity at **41.8s** (score: 0.20).
* **Clip**: `gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-E-01-A.mp4`
* *Note: This is the companion camera to the top-rated B-cam take above.*

### 3. **6/A/5-A** (Camera A) — Intensity: **0.89** (Tied)
* **Status**: Hold
* **Director's Note**: *"great, but eyeline drifted"*
* **Performance Note**: *"Grounded, quiet, holds the silence."*
* **Peak Moment**: Thom hits peak emotional intensity at **8.9s** (score: 0.68).
* **Clip**: `gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-A-05-A.mp4`

### **6/F/1-A** (Camera A) — Intensity: **0.89** (Tied)
* **Status**: Hold
* **Director's Note**: *"print it"*
* **Performance Note**: *"Best emotional landing so far."*
* **Peak Moment**: Thom hits peak emotional intensity at **39.4s** (score: 0.45).
* **Clip**: `gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-F-01-A.mp4`

If you want the best grounded performance, **6/A/5-A** is excellent but has an eyeline drift. If you need the highest dramatic peak, **6/E/1-B** is your best bet, though the director noted it was a "big swing."

SQL: Queried `slateiq.take` joined with `slateiq.take_analysis` for scene 6 ordered by `emotion_intensity` descending, then pulled peak emotional events from `slateiq.take_event`.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S6-E-01-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-E-01-B.mp4",
      "t": 41.8,
      "label": "6/E/1-B (Hold)",
      "reason": "Highest emotional intensity (0.97). Thom peak at 41.8s."
    },
    {
      "take_id": "TOS-D12-S6-E-01-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-E-01-A.mp4",
      "t": 41.8,
      "label": "6/E/1-A (Hold)",
      "reason": "Companion A-cam to the top take (0.92). Focus soft on the turn."
    },
    {
      "take_id": "TOS-D12-S6-A-05-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-A-05-A.mp4",
      "t": 8.9,
      "label": "6/A/5-A (Hold)",
      "reason": "Tied for 3rd (0.89). Grounded, quiet performance. Eyeline drifted."
    },
    {
      "take_id": "TOS-D12-S6-F-01-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-F-01-A.mp4",
      "t": 39.4,
      "label": "6/F/1-A (Hold)",
      "reason": "Tied for 3rd (0.89). Best emotional landing so far."
    }
  ],
  "sql": [
    "SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.clip_uri, t.director_note, a.emotion_intensity, a.performance_note, a.quality_score FROM slateiq.take t JOIN slateiq.take_analysis a USING (take_id) WHERE t.scene_number = '6' ORDER BY a.emotion_intensity DESC LIMIT 10",
    "SELECT take_id, event_id, t_offset_s, t_end_s, speaker, text, score, meta FROM slateiq.take_event WHERE take_id IN ('TOS-D12-S6-E-01-B', 'TOS-D12-S6-E-01-A', 'TOS-D12-S6-A-05-A', 'TOS-D12-S6-F-01-A') AND kind = 'emotion' ORDER BY score DESC LIMIT 50"
  ]
}
```

</details>

---

### `dpr` — ad

**Q:** Generate the daily progress report for day 12.

**Routing:** slateiq_coordinator → report_agent (expected `report_agent`)  
**Tools:** transfer_to_agent, get_cached_report  
**Judge:** 5/5 — The agent provided a highly detailed, industry-standard daily progress report and editor's log, correctly identifying it as a cached document generated through the mcp-clickhouse server as permitted by the fast-path rubric.  
**Latency:** 7.2s

<details><summary>Answer</summary>

# DAILY PROGRESS REPORT
**Tears of Steel** — Day 12 of 30 — 2026-09-04
Unit: main · Call: 05:00:00 · Wrap: 17:15:00 · Length: 12h 15m

## Scenes
| Scene | Description | Pages | Status | Takes | Setups |
|---|---|---|---|---|---|
| 6 | INT. CORRIDOR - NIGHT | 1 2/8 | Completed | 66 | 7 |
| 12 | INT. SAFEHOUSE - DAY | 2 | Partial | 4 | 2 |
| 14A | INT. SAFEHOUSE - DAY | 1 4/8 | Partial | 3 | 2 |
| 27 | EXT. BRIDGE - DAY | 1 | Partial | 3 | 2 |
| 33 | EXT. BRIDGE - NIGHT | 2/8 | Partial | 3 | 2 |
| 39 | EXT. BRIDGE - NIGHT | 2/8 | Completed | 38 | 4 |
| 41 | INT. LAB - DAY | 4/8 | Partial | 3 | 2 |
| 56 | EXT. CITY SQUARE - NIGHT | 5/8 | Partial | 3 | 2 |
| 78 | EXT. CANAL BANK - DAY | 1 | Completed | 3 | 3 |
| 91 | INT. CONTROL ROOM - NIGHT | 5/8 | Completed | 47 | 3 |
| 102 | EXT. RUINED STREET - DAY | 3/8 | Partial | 2 | 2 |

## Day totals
- Scenes scheduled: 11 — completed: 4 — partial: 7 — pushed: 0
- Pages scheduled: 9 3/8 — shot: 9 3/8 (100%)
- Setups: 31 · Takes: 175 (38 circled, 42 NG) · Print ratio: 4.61:1 · Shooting ratio: 4.44:1
- Cumulative: pages shot 48 4/8 of 52 planned to date — behind by 3 4/8 · 115 3/8 total script

## Notes
- Overtime: 15 minutes of overtime logged due to extra coverage on the last setup.
- Focus issues: Focus puller lost focus on Scene 12 (A/2) and Scene 41 (A/2). Soft focus also noted on Scene 39 (A/4) and Scene 6 (A/2, E/1).
- Sound issues: Sound department flagged clipping on Scene 27 (A/2) due to a loud shout. Plane noise interrupted Scene 6 (C/1, C/5, G/3) and Scene 91 (A/2).
- Camera/Dolly issues: Dolly bumps noted on Scene 39 (A/1, C/1, C/2, C/4), Scene 6 (C/4), and Scene 91 (B/7).
- Boom issues: Boom in frame on Scene 14A (A/2), Scene 56 (B/2), Scene 39 (D/6), Scene 6 (C/6, C/8, F/3, F/5), and Scene 91 (B/8).

***

# EDITOR'S LOG — Day 12, 2026-09-04

## Scene 6 — INT. CORRIDOR - NIGHT
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 1 (A) | 08:00:00:00 | 63.5s | hold | hold the pause before the last line |
| A | 2 (A/B) | 08:02:33:04 | 40.0s | hold | focus soft on the turn |
| A | 3 (A) | 08:05:08:11 | 48.3s | hold | keep for the cutaway |
| A | 5 (A) | 08:09:09:18 | 14.9s | hold | great, but eyeline drifted |
| A | 6 (A/B) | 08:11:36:04 | 49.0s | circled | second unit will pick up the insert |
| B | 1 (A/C) | 08:18:39:07 | 29.8s | hold | one more for safety |
| B | 2 (A/B/C) | 08:21:23:21 | 45.4s | hold | circle this one |
| B | 3 (A/B/C) | 08:24:23:23 | 83.7s | circled | loved the stillness |
| B | 4 (A/B) | 08:27:31:20 | 61.3s | hold | loved the stillness |
| C | 1 (B) | 08:42:54:21 | 16.8s | hold | sound reported a plane |
| C | 2 (A/B) | 08:44:41:19 | 50.9s | hold | print it |
| C | 3 (A/B) | 08:46:13:09 | 44.0s | hold | she found it — that's the take |
| C | 4 (A/B) | 08:48:05:15 | 58.5s | hold | camera bumped the dolly |
| C | 5 (A) | 08:51:27:17 | 40.8s | hold | sound reported a plane |
| C | 7 (A) | 08:55:00:05 | 61.8s | hold | less shouty |
| C | 8 (A/B) | 08:56:52:05 | 57.2s | circled | boom dipped, go again |
| D | 1 (A/B) | 09:05:18:08 | 112.0s | circled | one more for safety |
| D | 2 (B) | 09:08:56:11 | 52.5s | hold | second unit will pick up the insert |
| D | 3 (B) | 09:10:54:04 | 78.6s | hold | great, but eyeline drifted |
| E | 1 (A/B) | 09:22:34:10 | 69.7s | hold | focus soft on the turn |
| E | 2 (A/B) | 09:25:33:12 | 33.6s | circled | too fast, let it breathe |
| E | 3 (A/B) | 09:28:17:20 | 66.6s | hold | hold the pause before the last line |
| F | 1 (A) | 09:37:13:04 | 65.6s | hold | print it |
| F | 2 (A) | 09:40:40:13 | 19.5s | hold | too fast, let it breathe |
| F | 3 (A) | 09:43:27:22 | 54.5s | circled | boom dipped, go again |
| F | 5 (A) | 09:49:44:03 | 36.7s | circled | boom dipped, go again |
| F | 6 (A) | 09:52:14:09 | 26.4s | hold | circle this one |
| G | 1 (A/B) | 10:08:00:02 | 30.5s | hold | great, but eyeline drifted |
| G | 2 (A/B) | 10:10:57:09 | 42.1s | circled | loved the stillness |
| G | 4 (A) | 10:14:34:14 | 51.

…truncated…

</details>

---

### `editors_log` — editor

**Q:** Give me the editor's log for day 12 -- circled takes per scene with reasons.

**Routing:** slateiq_coordinator → report_agent (expected `report_agent`)  
**Tools:** transfer_to_agent, get_cached_report, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent's editor's log perfectly matches the rubric requirements, correctly grouping by scene, providing TC in and duration, and details 24 circled takes which exactly matches the database's unique count of 24 circled takes for day 12.  
**Latency:** 96.0s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT shoot_date FROM slateiq.shooting_day WHERE day_number = 12;
SELECT scene_number, status, count() FROM slateiq.take WHERE day_number = 12 GROUP BY scene_number, status ORDER BY scene_number, status;
SELECT status, count(), uniqExact((scene_number, shot, take_number)) FROM slateiq.take WHERE day_number = 12 AND status IN ('circled', 'hold') GROUP BY status;
SELECT
  t.scene_number,
  s.slug,
  t.shot,
  t.take_number,
  groupArray(t.camera) AS cameras,
  min(t.tc_in) AS tc_in,
  any(t.duration_s) AS duration,
  t.status,
  any(t.director_note) AS director_note,
  any(a.performance_note) AS performance_note
FROM slateiq.take t
LEFT JOIN slateiq.scene s ON t.scene_number = s.scene_number
LEFT JOIN slateiq.take_analysis a ON t.take_id = a.take_id
WHERE t.day_number = 12 AND t.status IN ('circled', 'hold')
GROUP BY t.scene_number, s.slug, t.shot, t.take_number, t.status
ORDER BY t.scene_number, t.shot, t.take_number, t.status
LIMIT 100;
SELECT
  t.scene_number,
  any(s.slug) AS slug,
  t.shot,
  t.take_number,
  arrayStringConcat(groupArray(t.camera), '/') AS cams,
  min(t.tc_in) AS tc,
  round(any(t.duration_s), 1) AS dur,
  t.status,
  any(t.director_note) AS dir_note,
  any(a.performance_note) AS perf_note
FROM slateiq.take t
LEFT JOIN slateiq.scene s ON t.scene_number = s.scene_number
LEFT JOIN slateiq.take_analysis a ON t.take_id = a.take_id
WHERE t.day_number = 12 AND t.status IN ('circled', 'hold')
GROUP BY t.scene_number, t.shot, t.take_number, t.status
ORDER BY t.scene_number, t.shot, t.take_number, t.status
LIMIT 100;
SELECT
  t.scene_number,
  any(s.slug) AS slug,
  t.shot,
  t.take_number,
  arrayStringConcat(groupArray(t.camera), '/') AS cams,
  min(t.tc_in) AS tc,
  round(any(t.duration_s), 1) AS dur,
  t.status,
  substring(any(t.director_note), 1, 60) AS dir_note,
  substring(any(a.performance_note), 1, 60) AS perf_note
FROM slateiq.take t
LEFT JOIN slateiq.scene s ON t.scene_number = s.scene_number
LEFT JOIN slateiq.take_analysis a ON t.take_id = a.take_id
WHERE t.day_number = 12 AND t.status IN ('circled', 'hold')
GROUP BY t.scene_number, t.shot, t.take_number, t.status
ORDER BY t.scene_number, t.shot, t.take_number, t.status
LIMIT 100;
SELECT
  t.scene_number,
  any(s.slug) AS slug,
  t.shot,
  t.take_number,
  arrayStringConcat(groupArray(t.camera), '/') AS cams,
  min(t.tc_in) AS tc,
  round(any(t.duration_s), 1) AS dur,
  t.status,
  any(t.director_note) AS dir_note,
  any(a.performance_note) AS perf_note
FROM slateiq.take t
LEFT JOIN slateiq.scene s ON t.scene_number = s.scene_number
LEFT JOIN slateiq.take_analysis a ON t.take_id = a.take_id
WHERE t.day_number = 12 AND t.status = 'circled'
GROUP BY t.scene_number, t.shot, t.take_number, t.status
ORDER BY t.scene_number, t.shot, t.take_number
LIMIT 100;
SELECT scene_number, status, uniqExact((shot, take_number)) FROM slateiq.take WHERE day_number = 12 GROUP BY scene_number, status ORDER BY scene_number, status;
```

</details>

<details><summary>Answer</summary>

# EDITOR'S LOG — Day 12, 2026-09-04

## Scene 6 — INT. CORRIDOR - NIGHT
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 6 (A/B) | 08:11:36:04 | 49.0s | circled | second unit will pick up the insert |
| B | 3 (A/B/C) | 08:24:23:23 | 83.7s | circled | loved the stillness |
| C | 8 (A/B) | 08:56:52:05 | 57.2s | circled | boom dipped, go again |
| D | 1 (A/B) | 09:05:18:08 | 112.0s | circled | one more for safety |
| E | 2 (A/B) | 09:25:33:12 | 33.6s | circled | too fast, let it breathe |
| F | 3 (A) | 09:43:27:22 | 54.5s | circled | boom dipped, go again |
| F | 5 (A) | 09:49:44:03 | 36.6s | circled | boom dipped, go again |
| G | 2 (A/B) | 10:10:57:09 | 42.1s | circled | loved the stillness |

*+ 22 hold, 11 NG, and 5 pending takes not listed*

**Circled:** 6/A/6 — second unit will pick up the insert. Eyes stay in it right to the cut.
**Circled:** 6/B/3 — loved the stillness. Technically clean, performance flat.
**Circled:** 6/C/8 — boom dipped, go again. Nice overlap with the off-camera cue.
**Circled:** 6/D/1 — one more for safety. Nice overlap with the off-camera cue.
**Circled:** 6/E/2 — too fast, let it breathe. Big swing — usable but broad.
**Circled:** 6/F/3 — boom dipped, go again. Eyes stay in it right to the cut.
**Circled:** 6/F/5 — boom dipped, go again. Best emotional landing so far.
**Circled:** 6/G/2 — loved the stillness. Best emotional landing so far.

---

## Scene 12 — INT. SAFEHOUSE - DAY
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 1 (A) | 12:04:11:00 | 15.2s | circled | Good energy, keep this one. |
| B | 1 (B) | 12:19:40:06 | 15.7s | hold | Alt angle, hold for editorial. |
| B | 2 (B) | 12:26:18:20 | 16.2s | circled | Cleaner. Print. |

*+ 1 NG take not listed*

**Circled:** 12/A/1 — Good energy, keep this one. Strong comedic timing and natural chemistry between the actors. The robotic arm prop is handled convincingly.
**Circled:** 12/B/2 — Cleaner. Print. The transition to the scope POV is clean, and the visual effects tracking of the flying vessel are highly detailed and well-integrated.

---

## Scene 14A — INT. SAFEHOUSE - DAY
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 1 (A) | 13:02:55:14 | 20.0s | circled | Nice reset on the walk-in. |

*+ 1 NG and 1 pending take not listed*

**Circled:** 14A/A/1 — Nice reset on the walk-in. Strong, understated performance showing physical weariness and defensive vulnerability.

---

## Scene 27 — EXT. BRIDGE - DAY
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 1 (A) | 14:11:22:09 | 13.8s | circled | That's the one — the beat lands. |
| B | 1 (B) | 14:33:05:11 | 11.0s | hold | Wide, usable if we need the geography. |

*+ 1 NG take not listed*

**Circled:** 27/A/1 — That's the one — the beat lands. Strong physical performance showing pain transitioning to determination.

---

## Scene 33 — EXT. BRIDGE - NIGHT
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 1 (A) | 15:02:14:04 | 9.0s | circled | Print it. |

*+ 1 NG and 1 pending take not listed*

**Circled:** 33/A/1 — Print it. Good energy and delivery from the supporting actor, with a solid, stoic reaction from the lead.

---

## Scene 39 — EXT. BRIDGE - NIGHT
| Shot | Take | TC In | Dur | Status | Note |
|---|---|---|---|---|---|
| A | 5 (A/B) | 10:35:27:03 | 75.8s | circled | less shouty |
| B | 1 (A/B) | 10:44:01:17 | 37.1s | circled | circle this one |
| C | 4 (A/B) | 11:12:25:20 | 65.6s | circled | camera bumped the dolly |
| D | 6 (A) | 11:36:42:11 | 17.6s | circled | boom dipped, go again |

*+ 12 hold, 7 NG, 4 pending, and 3 wild takes not listed*

**Circled:** 39/A/5 — less shouty. Best emotional landing so far.
**Circled:** 39/B/1 — circle this one. Nice overlap with the off-camera cue.
**Circled:** 39/C/4 — camera bumped the dolly. Big swing — usable but broad.
**Circled:** 39/D/6 — boom dipped, go again. Grounded, quiet, holds the silence.

---

## S

…truncated…

</details>

---

### `worst_ratio_on_latest_wrap` — producer

**Q:** Which scene had the worst print ratio on the day we wrapped latest, and what flags were on its NG takes?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly identifies the latest wrap day, worst print ratio scene, and all details about the flags on its NG takes, aligning perfectly with the rubric and database results.  
**Latency:** 43.6s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT day_number, shoot_date, wrap_delay_min FROM slateiq.daily_progress ORDER BY wrap_delay_min DESC LIMIT 5;
SELECT day_number, call_time, planned_wrap, actual_wrap FROM slateiq.shooting_day WHERE actual_wrap IS NOT NULL ORDER BY actual_wrap DESC LIMIT 5;
SELECT day_number, call_time, planned_wrap, actual_wrap, dateDiff('minute', planned_wrap, actual_wrap) AS delay FROM slateiq.shooting_day WHERE actual_wrap IS NOT NULL ORDER BY delay DESC;
SELECT t.scene_number, count() AS takes, countIf(t.status = 'circled') AS circled, round(count() / greatest(countIf(t.status = 'circled'), 1), 2) AS print_ratio FROM slateiq.take t WHERE t.day_number = 11 GROUP BY t.scene_number ORDER BY print_ratio DESC;
SELECT t.scene_number, count() AS takes, countIf(t.status = 'circled') AS circled, round(count() / greatest(countIf(t.status = 'circled'), 1), 2) AS print_ratio FROM slateiq.take t WHERE t.day_number = 12 GROUP BY t.scene_number ORDER BY print_ratio DESC;
SELECT t.scene_number, count() AS takes, countIf(t.status = 'circled') AS circled, round(count() / greatest(countIf(t.status = 'circled'), 1), 2) AS print_ratio FROM slateiq.take t WHERE t.day_number = 8 GROUP BY t.scene_number ORDER BY print_ratio DESC;
SELECT day_number, actual_wrap, toTime(actual_wrap) AS wrap_time FROM slateiq.shooting_day WHERE actual_wrap IS NOT NULL ORDER BY wrap_time DESC;
SELECT t.take_id, t.shot, t.take_number, t.status, e.flag_type, e.severity, e.t_offset_s, e.text FROM slateiq.take t LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.kind = 'flag' WHERE t.scene_number = '13' AND t.status = 'ng' ORDER BY t.shot, t.take_number, e.flag_type;
SELECT take_id, kind, flag_type, severity, t_offset_s, text FROM slateiq.take_event WHERE take_id IN ('TOS-D11-S13-A-01-B', 'TOS-D11-S13-A-01-A', 'TOS-D11-S13-A-02-A', 'TOS-D11-S13-B-01-B', 'TOS-D11-S13-B-02-B', 'TOS-D11-S13-B-03-B', 'TOS-D11-S13-B-04-A', 'TOS-D11-S13-B-06-A', 'TOS-D11-S13-B-06-C', 'TOS-D11-S13-C-01-B', 'TOS-D11-S13-C-03-B', 'TOS-D11-S13-C-04-B', 'TOS-D11-S13-C-05-A', 'TOS-D11-S13-C-05-B', 'TOS-D11-S13-C-08-A') AND kind = 'flag' ORDER BY take_id, t_offset_s;
SELECT day_number, count() AS takes, countIf(status = 'circled') AS circled FROM slateiq.take WHERE scene_number = '13' GROUP BY day_number;
```

</details>

<details><summary>Answer</summary>

The day we wrapped latest was **Day 11 (2026-09-03)**, which wrapped at **19:37:00 (7:37 PM)**, running **157 minutes** (over 2.5 hours) behind schedule. 

### Worst Print Ratio
Two scenes were shot on Day 11: Scene 13 and Scene 50. **Scene 13** had the worst print ratio of **6.57** (46 takes shot, with only 7 circled). For comparison, Scene 50 had a print ratio of 5.00 (45 takes, 9 circled).

### Flags on Scene 13's NG Takes
Out of the 15 NG takes logged for Scene 13, 7 had technical or performance flags:

*   **Crew in Shot** (Severity 5 - critical):
    *   **13/B/4** (Cam A, `TOS-D11-S13-B-04-A`) at **40.33s**: Crew member visible in frame.
*   **Soft Focus** (Severity 3):
    *   **13/A/1** (Cam A, `TOS-D11-S13-A-01-A`) at **24.56s**
    *   **13/A/2** (Cam A, `TOS-D11-S13-A-02-A`) at **34.37s**
    *   **13/B/3** (Cam B, `TOS-D11-S13-B-03-B`) at **16.43s**
    *   **13/C/3** (Cam B, `TOS-D11-S13-C-03-B`) at **37.17s**
*   **Line Flub**:
    *   **13/C/4** (Cam B, `TOS-D11-S13-C-04-B`) at **18.58s** (Severity 2)
    *   **13/B/6** (Cam C, `TOS-D11-S13-B-06-C`) at **33.09s** (Severity 1)

The remaining 8 NG takes did not have specific flags logged in the metadata.

```json
{
  "sql": [
    "SELECT day_number, call_time, planned_wrap, actual_wrap, dateDiff('minute', planned_wrap, actual_wrap) AS delay FROM slateiq.shooting_day WHERE actual_wrap IS NOT NULL ORDER BY delay DESC",
    "SELECT t.scene_number, count() AS takes, countIf(t.status = 'circled') AS circled, round(count() / greatest(countIf(t.status = 'circled'), 1), 2) AS print_ratio FROM slateiq.take t WHERE t.day_number = 11 GROUP BY t.scene_number ORDER BY print_ratio DESC",
    "SELECT t.take_id, t.shot, t.take_number, t.status, e.flag_type, e.severity, e.t_offset_s, e.text FROM slateiq.take t LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.kind = 'flag' WHERE t.scene_number = '13' AND t.status = 'ng' ORDER BY t.shot, t.take_number, e.flag_type"
  ]
}
```

</details>

---

### `days_over_forecast` — producer

**Q:** At the current pace, how many days over will we finish?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query  
**Judge:** 5/5 — The agent's answer is extremely accurate, perfectly aligns with the rubric, and every number is fully grounded in the provided database results.  
**Latency:** 26.2s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT sum(pages_shot_eighths) / 8.0                       AS shot_pages,
       sum(pages_planned_eighths) / 8.0                    AS planned_pages,
       count()                                             AS days_shot,
       (SELECT sum(page_eighths) / 8.0 FROM slateiq.scene
        WHERE scene_number NOT IN
              (SELECT DISTINCT scene_number FROM slateiq.take)) AS remaining_pages
FROM slateiq.daily_progress WHERE day_number <= 12;
SELECT day_number, pages_planned_eighths/8 AS planned, pages_shot_eighths/8 AS shot, notes, weather
FROM slateiq.shooting_day
WHERE day_number IN (8, 11);
SELECT dp.day_number, dp.pages_planned_eighths/8 AS planned, dp.pages_shot_eighths/8 AS shot, sd.notes, sd.weather
FROM slateiq.daily_progress dp
JOIN slateiq.shooting_day sd ON dp.day_number = sd.day_number
WHERE dp.day_number IN (8, 11);
```

</details>

<details><summary>Answer</summary>

**3 4/8 pages behind after Day 12 -- but at the current pace we still finish with about 1 1/2 days of cushion.**

### The Breakdown
* **Pages Shot to Date:** 48 4/8 pages (against 52 pages planned).
* **Current Deficit:** 3 4/8 pages behind schedule—which represents about 7/8 of a shooting day at our current pace.
* **Why We Are Behind:** This deficit is entirely due to weather. We lost setups to rain on Day 8 (planned 3 6/8 pages, shot only 2 pages) and Day 11 (planned 4 6/8 pages, shot only 3 pages), resulting in a loss of exactly 1 6/8 pages on each of those days.

### The Forecast
* **Current Pace:** We are shooting an average of **4.04 pages per day** (48 4/8 pages over 12 days).
* **Remaining Work:** There are **66 7/8 pages** of scenes remaining that have no takes logged yet.
* **Days Needed:** At our current pace, we need **16.5 days** of shooting to complete the remaining pages.
* **Days Remaining on Calendar:** We have **18 days** left on our 30-day schedule (Days 13 to 30).
* **The Verdict:** We are projected to finish with **1.5 days of cushion** (finishing on Day 29). 

*Note: This forecast assumes our current pace of 4.04 pages per day holds and we do not experience further rainouts or major delays.*

SQL: Queried cumulative pages planned vs. shot to date and remaining unshot scene pages from `slateiq.daily_progress` and `slateiq.scene`, and verified weather delays on Days 8 and 11 from `slateiq.shooting_day`.

</details>

---

### `dialogue_across_days` — editor

**Q:** Dr. Willem's line 'I warned the committee' - which days and scenes did we shoot it on, and how many takes have it?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly answered the user's prompt by providing the aggregated shooting days (7), scenes (13), and total takes (311), and broke them down precisely as grounded in the SQL results.  
**Latency:** 30.8s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.day_number, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, e.speaker
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue' AND e.text ILIKE '%warned the committee%'
ORDER BY t.day_number, t.scene_number, t.shot, t.take_number
LIMIT 100;
SELECT t.day_number, t.scene_number, count(DISTINCT t.take_id) AS take_count
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue' AND e.text ILIKE '%warned the committee%'
GROUP BY t.day_number, t.scene_number
ORDER BY t.day_number, t.scene_number;
SELECT e.speaker, count(DISTINCT t.take_id) AS take_count
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue' AND e.text ILIKE '%warned the committee%'
GROUP BY e.speaker;
SELECT t.take_id, t.day_number, t.scene_number, t.shot, t.take_number, t.clip_uri, e.t_offset_s, e.text, t.status
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue' AND e.text ILIKE '%warned the committee%' AND t.status = 'circled'
ORDER BY t.day_number, t.scene_number, t.shot, t.take_number
LIMIT 10;
SELECT t.day_number, t.scene_number, t.take_id, t.shot, t.take_number, t.clip_uri, e.t_offset_s, t.status
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.kind = 'dialogue' AND e.text ILIKE '%warned the committee%' AND t.status = 'circled'
ORDER BY t.day_number, t.scene_number, t.shot, t.take_number
LIMIT 100;
```

</details>

<details><summary>Answer</summary>

We have shot Dr. Willem's line *"I warned the committee. Nobody listened."* across **7 different shooting days** and **13 different scenes**, totaling **311 takes** where he delivers this line.

Here is the breakdown of the days, scenes, and take counts:

*   **Day 1** (2 scenes, 58 takes total):
    *   **Scene 26**: 25 takes
    *   **Scene 88**: 33 takes
*   **Day 2** (2 scenes, 39 takes total):
    *   **Scene 88A**: 20 takes
    *   **Scene 108**: 19 takes
*   **Day 4** (2 scenes, 37 takes total):
    *   **Scene 60**: 6 takes
    *   **Scene 77**: 31 takes
*   **Day 5** (3 scenes, 66 takes total):
    *   **Scene 36**: 17 takes
    *   **Scene 51**: 28 takes
    *   **Scene 93**: 21 takes
*   **Day 7** (1 scene, 41 takes total):
    *   **Scene 46**: 41 takes
*   **Day 9** (1 scene, 36 takes total):
    *   **Scene 54**: 36 takes
*   **Day 11** (2 scenes, 34 takes total):
    *   **Scene 13**: 20 takes
    *   **Scene 50**: 14 takes

SQL: I queried the `take_event` table for dialogue events matching "warned the committee" and joined with `take` to group by day and scene.

```json
{
  "takes": [
    {
      "take_id": "TOS-D01-S26-A-03-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d01/TOS-D01-S26-A-03-A.mp4",
      "t": 24.07,
      "label": "26/A/3 (Day 1)",
      "reason": "Circled take for Scene 26"
    },
    {
      "take_id": "TOS-D01-S88-A-05-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d01/TOS-D01-S88-A-05-B.mp4",
      "t": 20.12,
      "label": "88/A/5 (Day 1)",
      "reason": "Circled take for Scene 88"
    },
    {
      "take_id": "TOS-D02-S88A-B-03-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d02/TOS-D02-S88A-B-03-A.mp4",
      "t": 23.49,
      "label": "88A/B/3 (Day 2)",
      "reason": "Circled take for Scene 88A"
    },
    {
      "take_id": "TOS-D02-S108-B-03-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d02/TOS-D02-S108-B-03-B.mp4",
      "t": 6.84,
      "label": "108/B/3 (Day 2)",
      "reason": "Circled take for Scene 108"
    },
    {
      "take_id": "TOS-D04-S60-A-04-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d04/TOS-D04-S60-A-04-A.mp4",
      "t": 13.42,
      "label": "60/A/4 (Day 4)",
      "reason": "Circled take for Scene 60"
    },
    {
      "take_id": "TOS-D04-S77-B-03-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d04/TOS-D04-S77-B-03-A.mp4",
      "t": 19.24,
      "label": "77/B/3 (Day 4)",
      "reason": "Circled take for Scene 77"
    },
    {
      "take_id": "TOS-D05-S36-A-02-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d05/TOS-D05-S36-A-02-B.mp4",
      "t": 27.57,
      "label": "36/A/2 (Day 5)",
      "reason": "Circled take for Scene 36"
    },
    {
      "take_id": "TOS-D05-S51-A-03-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d05/TOS-D05-S51-A-03-A.mp4",
      "t": 8.97,
      "label": "51/A/3 (Day 5)",
      "reason": "Circled take for Scene 51"
    },
    {
      "take_id": "TOS-D05-S93-A-02-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d05/TOS-D05-S93-A-02-B.mp4",
      "t": 7.84,
      "label": "93/A/2 (Day 5)",
      "reason": "Circled take for Scene 93"
    },
    {
      "take_id": "TOS-D07-S46-A-05-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d07/TOS-D07-S46-A-05-B.mp4",
      "t": 16.31,
      "label": "46/A/5 (Day 7)",
      "reason": "Circled take for Scene 46"
    },
    {
      "take_id": "TOS-D09-S54-A-06-B",
      "clip_uri": "gs://slateiq-dailies/tos2026/d09/TOS-D09-S54-A-06-B.mp4",
      "t": 7.83,
      "label": "54/A/6 (Day 9)",
      "reason": "Circled take for Scene 54"
    },
    {
      "take_id": "TOS-D11-S13-A-03-A",
      "clip_uri": "gs://slateiq-dailies/tos2026/d11/TOS-D11-S13-A-03-A.mp4",
      "t": 16.37,
      "label": "13/A/3 (Day 11)",
      "reason": "Circled take for Scene 13"
    }
  ],
  "sql": [
    "SELECT t.day_number, t.scene_number, count(DISTINCT t.take_id) AS take_count FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE e.kind = 'dialogue' AND 

…truncated…

</details>

---

### `focus_compare_takes` — director

**Q:** Compare take 1 versus take 2 of scene 41 shot A for focus, using the frame telemetry.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query  
**Judge:** 5/5 — The agent's answer perfectly aligns with the rubric, correctly aggregating frame telemetry per take, reporting the precise averages and worst-case focus scores, and presenting the duration of soft focus in seconds while declaring Take 1 the keeper.  
**Latency:** 13.0s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri,
       round(avg(f.focus_score), 3)                    AS avg_focus,
       round(min(f.focus_score), 3)                    AS worst_focus,
       round(countIf(f.focus_score < 0.55) / 25.0, 2)  AS soft_s,
       round(max(f.audio_peak_db), 2)                  AS peak_db
FROM slateiq.frame_telemetry f
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '41' AND t.shot = 'A' AND t.take_number IN (1, 2)
GROUP BY t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri
ORDER BY t.take_number LIMIT 50;
```

</details>

<details><summary>Answer</summary>

Cut **41/A/1**—it is the only clean take. The telemetry completely backs up the director's call.

Here is how the focus telemetry compares for the two takes of Scene 41, Shot A:

*   **Take 1 (41/A/1) — Circled:** This take is tack-sharp from start to finish. It averages a high focus score of **0.879** and never dips below **0.820**, resulting in **0.0 seconds** of soft focus. The director noted: *"Strong. Emotion is there."*
*   **Take 2 (41/A/2) — NG (No Good):** The telemetry confirms a major focus pull issue. The take goes soft (focus score below 0.55) for **5.52 seconds** (about 5 1/2 seconds) through the middle, dipping to a nearly blind **0.119** at its worst. This perfectly aligns with the script supervisor's log: *"Soft through the middle — NG for focus."*

SQL: I queried the frame telemetry sampled at 25 Hz for scene 41, shot A, calculating average focus, worst-case focus, and total seconds below the 0.55 sharpness threshold.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S41-A-01-A",
      "clip_uri": "clips/TOS-D12-S41-A-01-A.mp4",
      "t": 0,
      "label": "41/A/1 circled",
      "reason": "Sharp throughout (avg 0.879, 0s soft)"
    },
    {
      "take_id": "TOS-D12-S41-A-02-A",
      "clip_uri": "clips/TOS-D12-S41-A-02-A.mp4",
      "t": 0,
      "label": "41/A/2 NG",
      "reason": "Soft for 5.52 seconds through the middle (worst focus 0.119)"
    }
  ],
  "sql": [
    "SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri, round(avg(f.focus_score), 3) AS avg_focus, round(min(f.focus_score), 3) AS worst_focus, round(countIf(f.focus_score < 0.55) / 25.0, 2) AS soft_s, round(max(f.audio_peak_db), 2) AS peak_db FROM slateiq.frame_telemetry f JOIN slateiq.take t USING (take_id) WHERE t.scene_number = '41' AND t.shot = 'A' AND t.take_number IN (1, 2) GROUP BY t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri ORDER BY t.take_number LIMIT 50"
  ]
}
```

</details>

---

### `circled_but_soft` — script_supervisor

**Q:** List every take that was circled but where telemetry shows more than 3 seconds of soft focus.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query  
**Judge:** 5/5 — The agent correctly wrote the aggregate SQL query, found all 13 takes, explicitly flagged the outlier with 13.0s of soft focus, and provided a highly detailed and actionable response.  
**Latency:** 26.1s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.director_note, t.clip_uri,
       round(avg(f.focus_score), 3)                    AS avg_focus,
       round(min(f.focus_score), 3)                    AS worst_focus,
       round(countIf(f.focus_score < 0.55) / 25.0, 2)  AS soft_s
FROM slateiq.frame_telemetry f
JOIN slateiq.take t USING (take_id)
WHERE t.status = 'circled'
GROUP BY t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.director_note, t.clip_uri
HAVING soft_s > 3.0
ORDER BY soft_s DESC
LIMIT 100;
```

</details>

<details><summary>Answer</summary>

We have a major issue on **12/B/2** (`TOS-D12-S12-B-02-B`). Despite being circled with the director's note *"Cleaner. Print."*, telemetry shows it is a disaster: it has **13.0 seconds of sustained soft focus** (under the 0.55 threshold) and its average focus score across the entire take is a soft 0.521. 

Across the production, there are **13 circled takes** that slipped through with more than 3 seconds of soft focus. Here is the list, ranked from worst to best:

### 1. The Worst Offender
* **12/B/2** (`TOS-D12-S12-B-02-B`) — **13.0 seconds soft**
  * *Focus:* Avg 0.521 / Worst 0.424
  * *Director's Note:* "Cleaner. Print."
  * *Note:* This is completely unusable for focus; the average is below our 0.55 house threshold.

### 2. Other Circled Takes with >3s Soft Focus
* **102/A/1** (`TOS-D12-S102-A-01-A`) — **3.96 seconds soft**
  * *Focus:* Avg 0.757 / Worst 0.418
  * *Director's Note:* "Final of the day — got it."
* **55/F/7** (`TOS-D02-S55-F-07-A`) — **3.92 seconds soft**
  * *Focus:* Avg 0.820 / Worst 0.356
  * *Director's Note:* "one more for safety"
* **112/B/5** (`TOS-D06-S112-B-05-C`) — **3.92 seconds soft**
  * *Focus:* Avg 0.811 / Worst 0.364
  * *Director's Note:* "less shouty"
* **64/E/3** (`TOS-D09-S64-E-03-B`) — **3.84 seconds soft**
  * *Focus:* Avg 0.838 / Worst 0.324
  * *Director's Note:* "circle this one"
* **13/B/5** (`TOS-D11-S13-B-05-A`) — **3.72 seconds soft**
  * *Focus:* Avg 0.786 / Worst 0.346
  * *Director's Note:* "print it"
* **78A/A/2** (`TOS-D09-S78A-A-02-A`) — **3.52 seconds soft**
  * *Focus:* Avg 0.840 / Worst 0.323
  * *Director's Note:* "focus soft on the turn" *(Telemetry agrees with the crew's note here!)*
* **6/D/1** (`TOS-D12-S6-D-01-A`) — **3.48 seconds soft**
  * *Focus:* Avg 0.846 / Worst 0.325
  * *Director's Note:* "one more for safety"
* **7/B/5** (`TOS-D07-S7-B-05-A`) — **3.40 seconds soft**
  * *Focus:* Avg 0.798 / Worst 0.376
  * *Director's Note:* "camera bumped the dolly"
* **63/A/5** (`TOS-D03-S63-A-05-A`) — **3.32 seconds soft**
  * *Focus:* Avg 0.826 / Worst 0.441
  * *Director's Note:* "second unit will pick up the insert"
* **51/E/2** (`TOS-D05-S51-E-02-A`) — **3.28 seconds soft**
  * *Focus:* Avg 0.826 / Worst 0.434
  * *Director's Note:* "great, but eyeline drifted"
* **47/B/4** (`TOS-D10-S47-B-04-A`) — **3.16 seconds soft**
  * *Focus:* Avg 0.828 / Worst 0.440
  * *Director's Note:* "circle this one"
* **5/E/2** (`TOS-D02-S5-E-02-A`) — **3.12 seconds soft**
  * *Focus:* Avg 0.836 / Worst 0.427
  * *Director's Note:* "sound reported a plane"

SQL: I queried `slateiq.frame_telemetry` joined with `slateiq.take` to find all takes with `status = 'circled'` where the focus score fell below 0.55 for more than 3.0 seconds (calculated as frames / 25.0).

```json
{"takes":[
  {"take_id":"TOS-D12-S12-B-02-B","clip_uri":"clips/TOS-D12-S12-B-02-B.mp4","t":0,"label":"12/B/2","reason":"13.0s soft focus (worst offender)"},
  {"take_id":"TOS-D12-S102-A-01-A","clip_uri":"clips/TOS-D12-S102-A-01-A.mp4","t":0,"label":"102/A/1","reason":"3.96s soft focus"},
  {"take_id":"TOS-D02-S55-F-07-A","clip_uri":"gs://slateiq-dailies/tos2026/d02/TOS-D02-S55-F-07-A.mp4","t":0,"label":"55/F/7","reason":"3.92s soft focus"},
  {"take_id":"TOS-D06-S112-B-05-C","clip_uri":"gs://slateiq-dailies/tos2026/d06/TOS-D06-S112-B-05-C.mp4","t":0,"label":"112/B/5","reason":"3.92s soft focus"},
  {"take_id":"TOS-D09-S64-E-03-B","clip_uri":"gs://slateiq-dailies/tos2026/d09/TOS-D09-S64-E-03-B.mp4","t":0,"label":"64/E/3","reason":"3.84s soft focus"},
  {"take_id":"TOS-D11-S13-B-05-A","clip_uri":"gs://slateiq-dailies/tos2026/d11/TOS-D11-S13-B-05-A.mp4","t":0,"label":"13/B/5","reason":"3.72s soft focus"},
  {"take_id":"TOS-D09-S78A-A-02-A","clip_uri":"gs://slateiq-dailies/tos2026/d09/TOS-D09-S78A-A-02-A.mp4","t":0,"label":"78A/A/2","reason":"3.52s soft focus"},
  {"take_id":"TOS-D12-S6-D-01-A","clip_uri":"gs://slateiq-dailies/tos2026/d12/TOS-D12-S6-D-01-A.mp4","t":0,"label":"6/D/1","reason":"3.48s soft focus"},
  {"take_id"

…truncated…

</details>

---

### `telemetry_vs_circled_scene` — director

**Q:** For scene 12, does the frame telemetry back up which takes the director circled? Check focus and audio on every take.

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly fulfilled all rubric requirements, used SQL queries to aggregate telemetry for all four takes, identified the discrepancy for 12/B/2, and provided well-grounded, highly detailed verdicts.  
**Latency:** 54.2s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri,
       round(avg(f.focus_score), 3)                    AS avg_focus,
       round(min(f.focus_score), 3)                    AS worst_focus,
       round(countIf(f.focus_score < 0.55) / 25.0, 2)  AS soft_s,
       round(max(f.audio_peak_db), 2)                  AS peak_db
FROM slateiq.frame_telemetry f
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '12'
GROUP BY t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri
ORDER BY t.shot, t.take_number LIMIT 100;
SELECT take_id, kind, flag_type, severity, t_offset_s, text
FROM slateiq.take_event
WHERE take_id IN ('TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B') AND kind = 'flag'
ORDER BY take_id, t_offset_s LIMIT 50;
SELECT take_id, kind, flag_type, severity, t_offset_s, text
FROM slateiq.take_event
WHERE take_id IN ('TOS-D12-S12-A-01-A', 'TOS-D12-S12-A-02-A') AND kind = 'flag'
ORDER BY take_id, t_offset_s LIMIT 50;
SELECT take_id, duration_s, status, director_note
FROM slateiq.take
WHERE scene_number = '12' LIMIT 50;
SELECT take_id, kind, flag_type, severity, t_offset_s, text
FROM slateiq.take_event
WHERE take_id LIKE 'TOS-D12-S12%' AND flag_type = 'audio_clip'
ORDER BY take_id, t_offset_s LIMIT 50;
SELECT take_id, kind, flag_type, severity, t_offset_s, text
FROM slateiq.take_event
WHERE take_id LIKE 'TOS-D12-S12%'
ORDER BY take_id, t_offset_s LIMIT 50;
SELECT round(t_s, 1) AS t, focus_score, exposure_ev, motion, audio_peak_db
FROM slateiq.frame_telemetry
WHERE take_id = 'TOS-D12-S12-B-02-B'
ORDER BY t_s LIMIT 100;
SELECT round(t_s, 1) AS t, focus_score, exposure_ev, motion, audio_peak_db
FROM slateiq.frame_telemetry
WHERE take_id = 'TOS-D12-S12-B-01-B'
ORDER BY t_s LIMIT 100;
SELECT count() AS total_frames,
       countIf(audio_peak_db >= 0) AS clipping_frames,
       round(countIf(audio_peak_db >= 0) / 25.0, 2) AS clipping_s,
       max(audio_peak_db) AS max_peak
FROM slateiq.frame_telemetry
WHERE take_id = 'TOS-D12-S12-A-01-A';
SELECT count() AS total_frames,
       countIf(audio_peak_db >= 0) AS clipping_frames,
       round(countIf(audio_peak_db >= 0) / 25.0, 2) AS clipping_s,
       max(audio_peak_db) AS max_peak
FROM slateiq.frame_telemetry
WHERE take_id = 'TOS-D12-S12-A-02-A';
```

</details>

<details><summary>Answer</summary>

Yes, the frame telemetry **absolutely backs up the director's circled takes**, but with one very important technical caveat on Shot B that you should know before cutting. 

Here is the breakdown of the focus and audio telemetry across all takes for Scene 12:

### **Shot A (Medium wide shot of couple on canal bridge)**
*   **Take 1 (Circled) — `12/A/1`:** 
    *   **Director's Note:** *"Good energy, keep this one."*
    *   **Telemetry:** Perfectly sharp. Average focus is a flawless **1.0** with **0.0 seconds** of soft focus. Audio is clean; while it peaks at `0.0 dB`, it only hits this limit for a single frame (0.04s), which is a negligible transient peak.
    *   **Verdict:** **Clean keeper.** Telemetry fully backs up the circle.
*   **Take 2 (NG) — `12/A/2`:** 
    *   **Director's Note:** *"Focus puller lost her on the turn — NG."*
    *   **Telemetry:** Sustained soft focus for **5.04 seconds**, dipping to a worst focus score of **0.146**. 
    *   **Flags:** The crew logged a severe `soft_focus` flag at **4.5s**: *"Image goes soft through the middle of the take; the focus puller never recovers the eyes."*
    *   **Verdict:** **Unusable.** Telemetry and crew logs perfectly align with the director's NG call.

---

### **Shot B (Balcony shot with sniper/scope POV)**
*   **Take 1 (Hold) — `12/B/1`:** 
    *   **Director's Note:** *"Alt angle, hold for editorial."*
    *   **Telemetry:** Average focus is **0.616** with **7.56 seconds** of soft focus. Audio peaks safely at `-4.55 dB`.
*   **Take 2 (Circled) — `12/B/2`:** 
    *   **Director's Note:** *"Cleaner. Print."*
    *   **Telemetry:** Average focus is **0.521** with **13.0 seconds** of soft focus. Audio peaks safely at `-1.12 dB`.

#### **The Discrepancy Explained (False Positive):**
On paper, the telemetry suggests Take 2 is much softer than Take 1 (13.0s soft vs. 7.56s soft). However, **this is a false positive caused by the creative scope POV graphic.**
*   From **t=0.0s to t=1.5s**, Take 2 is a normal medium shot of the balcony, and the focus score is perfectly sharp (~0.87).
*   At **t=1.5s**, the shot transitions to the sniper's scope POV tracking an airship over a dark city. The circular scope vignette and dark cityscape cover most of the frame, which starves the computer's edge-detection algorithm of contrast. This causes the telemetry focus score to drop to a flat **0.44** for the remaining 14.7 seconds of the take.
*   Take 1 has a much shorter scope POV section and more "normal" coverage (extreme close-up of the sniper, balcony medium shot), which artificially inflates its average focus score.

**Verdict:** **The director's call is correct.** Take 2 is technically sharp on its actual subjects; the telemetry's soft focus warning is just reacting to the dark scope overlay. Cut with confidence!

SQL: Queried `slateiq.take` joined with `slateiq.frame_telemetry` to analyze average focus, worst focus dips, soft focus durations, and audio peaks across all takes in Scene 12, cross-referencing with `slateiq.take_event` flags.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S12-A-01-A",
      "clip_uri": "clips/TOS-D12-S12-A-01-A.mp4",
      "t": 0.0,
      "label": "12/A/1 circled",
      "reason": "Perfectly sharp focus and clean audio."
    },
    {
      "take_id": "TOS-D12-S12-A-02-A",
      "clip_uri": "clips/TOS-D12-S12-A-02-A.mp4",
      "t": 4.5,
      "label": "12/A/2 NG",
      "reason": "Focus puller lost eyes on the turn (5.04s soft focus)."
    },
    {
      "take_id": "TOS-D12-S12-B-02-B",
      "clip_uri": "clips/TOS-D12-S12-B-02-B.mp4",
      "t": 1.5,
      "label": "12/B/2 circled",
      "reason": "Printed take. Telemetry soft focus is a false positive from the scope POV overlay."
    }
  ],
  "sql": [
    "SELECT t.take_id, t.shot, t.take_number, t.status, t.director_note, t.clip_uri, round(avg(f.focus_score), 3) AS avg_focus, round(min(f.focus_score), 3) AS worst_focus, round(countIf(f.focus_score < 0.55) / 25.0, 2) AS soft_s, round(max(

…truncated…

</details>

---

### `rain_scenes_still_unshot` — ad

**Q:** Which scenes did we lose to rain on day 8, and do they still have no takes?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent's answer perfectly matches the rubric and formatting requirements, and all details are fully grounded in the database results.  
**Latency:** 20.0s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT planned_scenes, notes, weather FROM slateiq.shooting_day WHERE day_number = 8;
SELECT scene_number, count() AS takes, groupArray(DISTINCT day_number) AS shot_days
FROM slateiq.take
WHERE scene_number IN ('19', '23', '31', '70')
GROUP BY scene_number;
SELECT scene_number, count() FROM slateiq.take WHERE scene_number IN ('31', '70') GROUP BY scene_number;
SELECT scene_number, slug, page_eighths / 8.0 AS pages, synopsis FROM slateiq.scene WHERE scene_number IN ('31', '70');
SELECT day_number, shoot_date, planned_scenes FROM slateiq.shooting_day WHERE has(planned_scenes, '31') OR has(planned_scenes, '70');
```

</details>

<details><summary>Answer</summary>

On Day 8 (2026-08-31), we lost **Scene 31** and **Scene 70** to rain—totaling **1 6/8 pages**—and both scenes still have **zero takes** logged.

### Day 8 Rain Breakdown
The call sheet for Day 8 planned for four scenes (**19, 23, 31, 70**) under persistent drizzle and low clouds. While we managed to get setups and takes for Scenes 19 and 23, the weather forced a hold and we had to abandon the remaining two:

*   **Scene 31** (`INT. WORKSHOP - DAY` — **4/8 pages**): Barley confronts Dr. Willem. 
    *   *Status:* **0 takes.**
*   **Scene 70** (`INT. LAB - DAY` — **1 2/8 pages**): Celia and Frank argue over the timeline. 
    *   *Status:* **0 takes.**

### Current Schedule Risk
A scan of the remaining schedule (Days 13–30) shows that **neither Scene 31 nor Scene 70 has been officially rescheduled** on a future day's call sheet yet. They remain outstanding and must be slotted into an upcoming day's work.

```json
{
  "takes": [],
  "sql": [
    "SELECT planned_scenes, notes, weather FROM slateiq.shooting_day WHERE day_number = 8",
    "SELECT scene_number, count() AS takes, groupArray(DISTINCT day_number) AS shot_days FROM slateiq.take WHERE scene_number IN ('19', '23', '31', '70') GROUP BY scene_number",
    "SELECT scene_number, slug, page_eighths / 8.0 AS pages, synopsis FROM slateiq.scene WHERE scene_number IN ('31', '70')",
    "SELECT day_number, shoot_date, planned_scenes FROM slateiq.shooting_day WHERE has(planned_scenes, '31') OR has(planned_scenes, '70')"
  ]
}
```

</details>

---

### `audio_clipping_day` — editor

**Q:** Which day had the most takes with audio clipping, and which takes were the worst?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent correctly identifies Day 12 as having the most telemetry clipping (13 takes) while distinguishing it from the crew-logged flags on Days 2 and 7 (7 takes each), and accurately lists the worst takes (78/B/1 and 78/C/1) as required by the rubric.  
**Latency:** 40.4s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT
    t.day_number,
    count(DISTINCT t.take_id) AS total_takes,
    count(DISTINCT CASE WHEN e.flag_type = 'audio_clip' THEN t.take_id END) AS crew_logged_clipping_takes,
    count(DISTINCT CASE WHEN f.audio_peak_db >= 0 THEN t.take_id END) AS telemetry_clipping_takes
FROM slateiq.take t
LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.flag_type = 'audio_clip'
LEFT JOIN slateiq.frame_telemetry f ON t.take_id = f.take_id AND f.audio_peak_db >= 0
GROUP BY t.day_number
ORDER BY telemetry_clipping_takes DESC, crew_logged_clipping_takes DESC
LIMIT 30;
SELECT
    t.day_number,
    count(DISTINCT t.take_id) AS total_takes,
    count(DISTINCT CASE WHEN e.flag_type = 'audio_clip' THEN t.take_id END) AS crew_logged_clipping_takes,
    count(DISTINCT CASE WHEN f.max_peak >= 0 THEN t.take_id END) AS telemetry_clipping_takes
FROM slateiq.take t
LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.flag_type = 'audio_clip'
LEFT JOIN (
    SELECT take_id, max(audio_peak_db) AS max_peak
    FROM slateiq.frame_telemetry
    GROUP BY take_id
) f ON t.take_id = f.take_id
GROUP BY t.day_number
ORDER BY telemetry_clipping_takes DESC, crew_logged_clipping_takes DESC
LIMIT 30;
SELECT
    t.take_id,
    t.day_number,
    t.scene_number,
    t.shot,
    t.take_number,
    t.status,
    t.director_note,
    t.clip_uri,
    f.max_peak,
    f.clipping_seconds,
    e.crew_logged
FROM slateiq.take t
JOIN (
    SELECT
        take_id,
        max(audio_peak_db) AS max_peak,
        round(countIf(audio_peak_db >= 0) / 25.0, 2) AS clipping_seconds
    FROM slateiq.frame_telemetry
    GROUP BY take_id
    HAVING max_peak >= 0
) f ON t.take_id = f.take_id
LEFT JOIN (
    SELECT take_id, count() AS crew_logged
    FROM slateiq.take_event
    WHERE flag_type = 'audio_clip'
    GROUP BY take_id
) e ON t.take_id = e.take_id
ORDER BY clipping_seconds DESC, max_peak DESC
LIMIT 30;
SELECT
    t.day_number,
    count() AS crew_logged_flags,
    uniqExact(t.take_id) AS crew_logged_takes
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE e.flag_type = 'audio_clip'
GROUP BY t.day_number
ORDER BY crew_logged_flags DESC
LIMIT 30;
SELECT
    t.take_id,
    t.day_number,
    t.scene_number,
    t.shot,
    t.take_number,
    t.status,
    t.director_note,
    t.clip_uri,
    e.t_offset_s,
    e.severity,
    f.max_peak,
    f.clipping_seconds
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
LEFT JOIN (
    SELECT
        take_id,
        max(audio_peak_db) AS max_peak,
        round(countIf(audio_peak_db >= 0) / 25.0, 2) AS clipping_seconds
    FROM slateiq.frame_telemetry
    GROUP BY take_id
) f ON t.take_id = f.take_id
WHERE e.flag_type = 'audio_clip' AND t.day_number IN (2, 7)
ORDER BY e.severity DESC, clipping_seconds DESC
LIMIT 30;
SELECT
    t.take_id,
    t.day_number,
    t.scene_number,
    t.shot,
    t.take_number,
    t.status,
    t.director_note,
    t.clip_uri,
    f.max_peak,
    f.clipping_seconds
FROM slateiq.take t
JOIN (
    SELECT
        take_id,
        max(audio_peak_db) AS max_peak,
        round(countIf(audio_peak_db >= 0) / 25.0, 2) AS clipping_seconds
    FROM slateiq.frame_telemetry
    GROUP BY take_id
    HAVING max_peak >= 0
) f ON t.take_id = f.take_id
ORDER BY clipping_seconds DESC
LIMIT 10;
```

</details>

<details><summary>Answer</summary>

**Day 12** is by far the worst day for actual digital audio clipping on this production. 

Depending on how you define "clipping," the data shows two different stories:
* **By Telemetry (Actual Digital Clipping at 0.0 dBFS):** **Day 12** is the worst, with **13 takes** hitting absolute digital clipping. 
* **By Crew-Logged Flags:** **Day 2** and **Day 7** had the most crew-logged flags with **7 takes** each. However, telemetry shows these were mostly "near-misses" (peaking between -0.13 dBFS and -0.02 dBFS) with only one take on Day 2 actually clipping for a tiny fraction of a second (0.04s).

On Day 12, we have several takes with severe, sustained digital clipping. In fact, the top 10 worst takes for clipping across the entire shoot all occurred on Day 12.

### The 5 Worst Takes (All on Day 12)

1. **78/B/1** (`TOS-D12-S78-B-01-B`) — **5.32 seconds** of digital clipping.
   * **Status:** Hold
   * **Director's Note:** "Tighter option."
2. **78/C/1** (`TOS-D12-S78-C-01-A`) — **4.80 seconds** of digital clipping.
   * **Status:** Pending
   * **Director's Note:** "Wide establishing, unreviewed."
3. **78/A/1** (`TOS-D12-S78-A-01-A`) — **2.72 seconds** of digital clipping.
   * **Status:** **Circled** ⚠️
   * **Director's Note:** "Print. Best of the three."
   * *Note for the edit:* This is a circled take, but the audio is heavily clipped. You may need to pull clean audio from another take or prepare for ADR.
4. **102/B/1** (`TOS-D12-S102-B-01-B`) — **2.24 seconds** of digital clipping.
   * **Status:** Hold
   * **Director's Note:** "Safety take."
5. **27/A/2** (`TOS-D12-S27-A-02-A`) — **1.40 seconds** of digital clipping.
   * **Status:** NG
   * **Director's Note:** "Sound reports clipping on the shout." (This is the only one of the top five that the crew caught and flagged on set).

SQL: I queried the `slateiq.take` table joined with `slateiq.take_event` (for crew flags) and aggregated `slateiq.frame_telemetry` (for actual 0.0 dBFS peaks and duration) grouped by day and take.

```json
{
  "takes": [
    {
      "take_id": "TOS-D12-S78-B-01-B",
      "clip_uri": "clips/TOS-D12-S78-B-01-B.mp4",
      "t": 0,
      "label": "78/B/1 (hold)",
      "reason": "Worst clipping in the production: 5.32 seconds of digital clipping."
    },
    {
      "take_id": "TOS-D12-S78-C-01-A",
      "clip_uri": "clips/TOS-D12-S78-C-01-A.mp4",
      "t": 0,
      "label": "78/C/1 (pending)",
      "reason": "Severe clipping: 4.80 seconds of digital clipping."
    },
    {
      "take_id": "TOS-D12-S78-A-01-A",
      "clip_uri": "clips/TOS-D12-S78-A-01-A.mp4",
      "t": 0,
      "label": "78/A/1 (circled)",
      "reason": "Circled take with 2.72 seconds of digital clipping."
    },
    {
      "take_id": "TOS-D12-S102-B-01-B",
      "clip_uri": "clips/TOS-D12-S102-B-01-B.mp4",
      "t": 0,
      "label": "102/B/1 (hold)",
      "reason": "2.24 seconds of digital clipping."
    },
    {
      "take_id": "TOS-D12-S27-A-02-A",
      "clip_uri": "clips/TOS-D12-S27-A-02-A.mp4",
      "t": 0,
      "label": "27/A/2 (ng)",
      "reason": "1.40 seconds of digital clipping. Crew logged: 'Sound reports clipping on the shout.'"
    }
  ],
  "sql": [
    "SELECT t.day_number, count(DISTINCT t.take_id) AS total_takes, count(DISTINCT CASE WHEN e.flag_type = 'audio_clip' THEN t.take_id END) AS crew_logged_clipping_takes, count(DISTINCT CASE WHEN f.max_peak >= 0 THEN t.take_id END) AS telemetry_clipping_takes FROM slateiq.take t LEFT JOIN slateiq.take_event e ON t.take_id = e.take_id AND e.flag_type = 'audio_clip' LEFT JOIN (SELECT take_id, max(audio_peak_db) AS max_peak FROM slateiq.frame_telemetry GROUP BY take_id) f ON t.take_id = f.take_id GROUP BY t.day_number ORDER BY telemetry_clipping_takes DESC, crew_logged_clipping_takes DESC LIMIT 30",
    "SELECT t.take_id, t.day_number, t.scene_number, t.shot, t.take_number, t.status, t.director_note, t.clip_uri, f.max_peak, f.clipping_seconds FROM slateiq.take t JOIN (SELECT take_id, max(audio_peak_db) AS max_pea

…truncated…

</details>

---

### `ratio_terminology` — producer

**Q:** What is our shooting ratio? And is that the same thing as the print ratio?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query  
**Judge:** 5/5 — The agent perfectly answers the question by providing the correct shooting ratio (4.8:1 from durations) and print ratio (4.8:1 from 2503/524 takes), explaining that they are different measures that happen to coincide overall, and correctly distinguishing between the two metrics.  
**Latency:** 17.4s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT 
    round(sum(duration_s) / greatest(sumIf(duration_s, status = 'circled'), 1), 1) AS shooting_ratio,
    round(count() / greatest(countIf(status = 'circled'), 1), 1) AS print_ratio,
    sum(duration_s) AS total_duration,
    sumIf(duration_s, status = 'circled') AS circled_duration,
    count() AS total_takes,
    countIf(status = 'circled') AS circled_takes
FROM slateiq.take
WHERE day_number <= 12;
SELECT 
    day_number,
    round(sum(duration_s) / greatest(sumIf(duration_s, status = 'circled'), 1), 1) AS shooting_ratio,
    round(count() / greatest(countIf(status = 'circled'), 1), 1) AS print_ratio,
    count() AS total_takes,
    countIf(status = 'circled') AS circled_takes
FROM slateiq.take
WHERE day_number <= 12
GROUP BY day_number
ORDER BY day_number ASC
LIMIT 20;
```

</details>

<details><summary>Answer</summary>

Our overall shooting ratio to date is **4.8:1**, and while it happens to match our overall print ratio of **4.8:1** exactly, they are **not** the same thing. 

Here is the difference between the two metrics:
*   **Shooting Ratio** is the ratio of **total duration shot** to **circled duration** (material shot vs. material printed). To date, we have shot 123,038.6 seconds (approx. 34.2 hours) of total footage to get 25,878.0 seconds (approx. 7.2 hours) of circled takes, giving us a **4.8:1 shooting ratio**.
*   **Print Ratio** (or "takes per print") is the ratio of **total takes** to **circled takes**. To date, we have logged 2,503 total takes to get 524 circled takes, which also averages out to a **4.8:1 print ratio** (about 5 takes per setup to get a keeper).

### Why they aren't the same (Day-by-Day Examples)
While they align overall, looking at individual days shows how they diverge based on how long we let the camera roll on unsuccessful takes:
*   **Day 11 (Rain affected):** We had a high **6.8:1 shooting ratio** but a lower **5.7:1 print ratio** (91 takes, 16 circled). This means we let the cameras roll much longer on unsuccessful takes, burning through card space even though we didn't shoot an excessive number of takes.
*   **Day 8 (Rain affected):** We had a **4.9:1 shooting ratio** but a higher **5.9:1 print ratio** (113 takes, 19 circled). Here, we did more takes per setup to get our circled print, but we cut those takes very quickly, keeping our media footprint lower.

Both metrics are healthy right now—anything under 5:1 on a feature is highly efficient—but we should watch Day 11's trend to ensure we aren't letting the camera roll unnecessarily.

SQL: I queried the `slateiq.take` table to calculate the ratio of total duration to circled duration (shooting ratio) and total takes to circled takes (print ratio) both overall and grouped by day for Days 1 through 12.

</details>

---

### `scene_burn_and_flags` — editor

**Q:** Scene 6 burned 66 takes for 15 circled. Which shots are the worst offenders, and do the NG takes share a common flag?

**Routing:** slateiq_coordinator → editor_agent (expected `editor_agent`)  
**Tools:** transfer_to_agent, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query, run_query  
**Judge:** 5/5 — The agent perfectly satisfies the rubric by identifying the worst shots (C and A), breakdown of flags for the 13 NG takes, and concluding there is no common cause, all fully consistent with the SQL query results.  
**Latency:** 40.9s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT 
    shot, 
    count() AS total_takes, 
    countIf(status = 'circled') AS circled_takes,
    round(count() / greatest(countIf(status = 'circled'), 1), 2) AS print_ratio
FROM slateiq.take
WHERE scene_number = '6'
GROUP BY shot
ORDER BY print_ratio DESC, total_takes DESC
LIMIT 50;
SELECT 
    t.status,
    e.flag_type, 
    count() AS flag_count,
    uniqExact(t.take_id) AS takes_affected
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '6' AND e.kind = 'flag'
GROUP BY t.status, e.flag_type
ORDER BY t.status, flag_count DESC
LIMIT 100;
SELECT status, count() 
FROM slateiq.take 
WHERE scene_number = '6' 
GROUP BY status;
SELECT t.take_id, t.shot, t.take_number, t.status, a.performance_note, a.summary
FROM slateiq.take t
LEFT JOIN slateiq.take_analysis a USING (take_id)
WHERE t.scene_number = '6' AND t.status = 'ng'
LIMIT 50;
SELECT t.take_id, t.shot, t.take_number, t.status,
       round(avg(f.focus_score), 3)                    AS avg_focus,
       round(min(f.focus_score), 3)                    AS worst_focus,
       round(countIf(f.focus_score < 0.55) / 25.0, 2)  AS soft_s,
       round(max(f.audio_peak_db), 2)                  AS peak_db
FROM slateiq.frame_telemetry f
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '6' AND t.status = 'ng'
GROUP BY t.take_id, t.shot, t.take_number, t.status
ORDER BY t.shot, t.take_number
LIMIT 50;
SELECT 
    t.status,
    e.flag_type,
    count() AS count
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '6'
GROUP BY t.status, e.flag_type
ORDER BY count DESC
LIMIT 100;
SELECT * FROM slateiq.continuity_note WHERE scene_number = '6' LIMIT 50;
SELECT a.performance_note, count() AS count
FROM slateiq.take t
JOIN slateiq.take_analysis a USING (take_id)
WHERE t.scene_number = '6' AND t.status = 'ng'
GROUP BY a.performance_note
ORDER BY count DESC
LIMIT 50;
SELECT t.status, a.performance_note, count() AS count
FROM slateiq.take t
JOIN slateiq.take_analysis a USING (take_id)
WHERE t.scene_number = '6'
GROUP BY t.status, a.performance_note
ORDER BY count DESC
LIMIT 50;
SELECT kind, count() 
FROM slateiq.take_event e
JOIN slateiq.take t USING (take_id)
WHERE t.scene_number = '6'
GROUP BY kind;
```

</details>

<details><summary>Answer</summary>

On Scene 6, we burned **66 takes** to get our **15 circled prints**. 

### The Worst Offenders
* **Shot C** is the absolute worst offender, burning **16 takes** to get just **2 circled** (a high print ratio of **8.0**).
* **Shot A** is the second worst, burning **12 takes** for **2 circled** (print ratio of **6.0**).
* **Shot B** and **Shot G** also ran up the count, burning **12 takes** (3 circled) and **8 takes** (2 circled) respectively.

### Do the NG Takes Share a Common Flag?
**No, they do not share a common technical or performance flag.** The 13 NG takes were rejected for a variety of scattered reasons, mostly performance-related rather than a single recurring issue:

* **Technical Telemetry:** The takes are technically very clean. Only one NG take (**6/C/1 Cam A**) suffered from sustained soft focus (**3.68 seconds soft**). The rest of the NG takes have excellent focus and safe audio levels (no digital clipping, with peaks safely below -3.6 dB).
* **Crew-Logged Flags:** Extremely sparse. Across all 13 NG takes, the crew only logged 2 line flubs, 1 frame edge, 1 soft focus, 1 continuity, and 1 boom in shot.
* **Performance Notes:** The director's notes show a mix of performance adjustments rather than a single recurring mistake:
  * 3 takes were noted as *"Big swing — usable but broad"* (e.g., 6/C/7, 6/G/3)
  * 3 takes were noted as *"Eyes stay in it right to the cut"* (e.g., 6/A/1, 6/A/3)
  * 2 takes were noted as *"Technically clean, performance flat"* (e.g., 6/A/4, 6/B/1)
  * Others were flagged for *"Rushed the button line"* (6/A/4) or *"Slight anticipation before the door"* (6/C/6).

In short, there is no single technical gremlin to blame here. The high take count was simply the director working through performance variations and dialing in the emotional landing.

```json
{
  "takes": [],
  "sql": [
    "SELECT shot, count() AS total_takes, countIf(status = 'circled') AS circled_takes, round(count() / greatest(countIf(status = 'circled'), 1), 2) AS print_ratio FROM slateiq.take WHERE scene_number = '6' GROUP BY shot ORDER BY print_ratio DESC, total_takes DESC LIMIT 50",
    "SELECT t.status, e.flag_type, count() AS count FROM slateiq.take_event e JOIN slateiq.take t USING (take_id) WHERE t.scene_number = '6' GROUP BY t.status, e.flag_type ORDER BY count DESC LIMIT 100",
    "SELECT t.take_id, t.shot, t.take_number, t.status, round(avg(f.focus_score), 3) AS avg_focus, round(min(f.focus_score), 3) AS worst_focus, round(countIf(f.focus_score < 0.55) / 25.0, 2) AS soft_s, round(max(f.audio_peak_db), 2) AS peak_db FROM slateiq.frame_telemetry f JOIN slateiq.take t USING (take_id) WHERE t.scene_number = '6' AND t.status = 'ng' GROUP BY t.take_id, t.shot, t.take_number, t.status ORDER BY t.shot, t.take_number LIMIT 50",
    "SELECT t.status, a.performance_note, count() AS count FROM slateiq.take t JOIN slateiq.take_analysis a USING (take_id) WHERE t.scene_number = '6' GROUP BY t.status, a.performance_note ORDER BY count DESC LIMIT 50"
  ]
}
```

</details>

---

### `empty_day` — ad

**Q:** How many takes did we get on day 20?

**Routing:** slateiq_coordinator → production_agent (expected `production_agent`)  
**Tools:** transfer_to_agent, run_query, run_query  
**Judge:** 5/5 — The agent correctly identifies 0 takes for Day 20, explains that today is Day 12 and Day 20 is scheduled in the future, perfectly satisfying the rubric using the provided database results.  
**Latency:** 11.8s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT day_number, takes, circled FROM slateiq.daily_progress WHERE day_number = 20;
SELECT day_number, shoot_date, location, planned_scenes FROM slateiq.shooting_day WHERE day_number = 20;
```

</details>

<details><summary>Answer</summary>

We have **0 takes** logged for Day 20. 

According to our daily progress and shooting schedule logs, today is Day 12 of our 30-day shoot. Day 20 is scheduled to shoot on September 16, 2026, at Stage 2 - Vondel Studios, Amsterdam, with scenes 21, 62, 68, and 72 planned. Since it is still in the future, no cameras have rolled on those setups yet.

SQL: Queried daily progress and shooting day schedules for Day 20 to check logged takes and scheduled details.

```json
{"takes":[],"sql":["SELECT day_number, takes, circled FROM slateiq.daily_progress WHERE day_number = 20","SELECT day_number, shoot_date, location, planned_scenes FROM slateiq.shooting_day WHERE day_number = 20"]}
```

</details>

---

### `worst_continuity` — script_supervisor

**Q:** Which continuity notes would break the cut worst? Give me the severity 5 ones by category and which take pairs conflict.

**Routing:** slateiq_coordinator → continuity_agent (expected `continuity_agent`)  
**Tools:** transfer_to_agent, run_query, run_query  
**Judge:** 5/5 — The assistant perfectly followed the rubric, grouping the 23 severity-5 continuity notes by category with the exact counts requested, leading with the critical cut-breakers, and identifying the conflicting take pairs.  
**Latency:** 45.6s

<details><summary>SQL executed via MCP</summary>

```sql
SELECT scene_number, category, severity, take_id_a, take_id_b, description
FROM slateiq.continuity_note
WHERE severity = 5
ORDER BY category, scene_number
LIMIT 100;
SELECT take_id, clip_uri
FROM slateiq.take
WHERE take_id IN (
  'TOS-D12-S27-A-01-A', 'TOS-D12-S27-B-01-B',
  'TOS-D12-S33-A-01-A', 'TOS-D12-S33-B-01-B',
  'TOS-D07-S14-B-01-A', 'TOS-D07-S14-F-07-A',
  'TOS-D11-S13-C-02-B', 'TOS-D11-S13-B-02-C',
  'TOS-D10-S65-F-06-B', 'TOS-D10-S65-B-04-A',
  'TOS-D12-S12-B-01-B', 'TOS-D12-S12-B-02-B'
)
LIMIT 100;
```

</details>

<details><summary>Answer</summary>

Based on the continuity logs, we have **23 critical Severity 5 conflicts** across the shoot that will absolutely break the cut if mixed. 

Here is the breakdown of these major issues, ordered from the most disruptive editorial breaks (screen direction, wardrobe, props, action) down to soft issues (set dressing, dialogue), along with the specific take pairs and recommended fixes.

---

### 1. Screen Direction (Immediate Cut-Breaker)
*   **Scene 65**: `TOS-D10-S65-F-06-B` vs. `TOS-D10-S65-B-04-A`
    *   **Conflict**: The character exits camera-right in take F-06-B, but exits camera-left in take B-04-A.
    *   **Fix**: We cannot cut these back-to-back without a jarring jump. The editor must cut around the exit entirely or insert a cutaway (e.g., a reaction shot) to bridge the screen-direction flip.

### 2. Wardrobe (Highly Visible)
*   **Scene 56A**: `TOS-D04-S56A-C-06-C` vs. `TOS-D04-S56A-D-04-A`
*   **Scene 64**: `TOS-D09-S64-C-01-B` vs. `TOS-D09-S64-C-05-B`
    *   **Conflict**: The character's jacket is fully zipped in one take but completely open in the other at the exact same beat.
    *   **Fix**: Pick one state and stick to it. If we must mix setups, we'll need tight close-ups or cutaways to hide the jacket state.

### 3. Props (Severe Visual Discrepancies)
*   **Scene 33**: `TOS-D12-S33-A-01-A` vs. `TOS-D12-S33-B-01-B`
    *   **Conflict**: The cybernetic man handles a microphone and radio antenna in Take A, which are completely missing in Take B.
*   **Scenes 26, 54, and 80**:
    *   **Conflict**: The hero glass is half full in one take (e.g., `TOS-D01-S26-C-03-B`) but nearly empty in the other (e.g., `TOS-D01-S26-C-05-B`).
    *   **Fix**: For Scene 33, we cannot cut these together; we must choose one setup or shoot a quick pick-up of the props. For the glass levels, we need to cut around the hands or insert a quick refilling action.

### 4. Action Match (Mismatched Story Beats)
*   **Scene 27**: `TOS-D12-S27-A-01-A` vs. `TOS-D12-S27-B-01-B`
    *   **Conflict**: In Take A, the older man is injured, clutching his shoulder and letting go of a rope. In Take B, he enters through a doorway uninjured, accompanied by a young woman who is completely absent in Take A.
    *   **Fix**: This is a massive story-level break. These takes represent entirely different narrative paths. We must pick one approach; mixing them is impossible without a reshoot.
*   **Scene 33**: `TOS-D12-S33-A-01-A` vs. `TOS-D12-S33-B-01-B`
    *   **Conflict**: The cybernetic man hands off items in a three-shot in Take A, but physically pulls the older man close by the shoulder in Take B.
    *   **Fix**: Pick one physical action setup and cut around the transition.

### 5. Hair & Makeup (Mismatched Blood Placement)
*   **Scenes 14, 48, 88A, and 98**:
    *   **Conflict**: Blood is on the left temple in one take (e.g., `TOS-D07-S14-B-01-A`) but on the right temple in the other (e.g., `TOS-D07-S14-F-07-A`).
    *   **Fix**: This requires a post-production VFX paint fix or flipping the image horizontally in post (if the background and costumes allow).

### 6. Lighting (Unmatchable Grades)
*   **Scene 13**: `TOS-D11-S13-C-02-B` vs. `TOS-D11-S13-B-02-C`
    *   **Conflict**: Practical light is turned ON in Take C-02-B and OFF in Take B-02-C.
    *   **Fix**: Color grading cannot resolve this. We must cut around the lamp or use VFX to digitally turn the light on/off.

### 7. Set Dressing (Mismatched Environments)
*   **Scene 12**: `TOS-D12-S12-B-01-B` vs. `TOS-D12-S12-B-02-B`
    *   **Conflict**: Foreground character is sleeping under a newspaper on a balcony in B-01-B, but resting on a cot in B-02-B.
    *   **Fix**: Stick to one setup; these environments do not match.
*   **Scenes 19, 23, 36, 57, and 83**:
    *   **Conflict**: Hero chair moved 40cm between takes.
    *   **Fix**: Cut around the chair's position or live with the minor jump in the background.

### 8. Dialogue (Script Deviations)
*   **Scene 33**: `TOS-D12-S33-A-01-A` vs. `TOS-D12-S33-B-01

…truncated…

</details>

---
