# `docs/` — design, evidence and review trail

Everything a reviewer needs to check the claims in the root [`README.md`](../README.md).

## Start here

| File | What |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | The system in detail: the shared `McpToolset`, coordinator → 4 specialists, the guardrail chain, the trace contract, and the ClickHouse schema the agent reasons over. The one doc to read if you only read one. |
| [`DEVPOST.md`](DEVPOST.md) | The submission write-up — problem, what it does, how it was built, every number re-verified. |
| [`PLAN.md`](PLAN.md) | The sprint plan the build followed. |
| [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) | Beat-by-beat cut of the trailer, synced to the committed **v2** (2:56.1), plus the ready-to-paste YouTube listing. |
| [`SUBMISSION.md`](SUBMISSION.md) | Submission checklist and status. |
| [`HANDOFF.md`](HANDOFF.md) | **The last mile, by hand** — YouTube upload, the Devpost form field by field, pre-submit checks, and what to do during the judging window. Vietnamese summary at the top. |

## Evidence trail

These are working documents, kept in the repo on purpose: they show what was found, what was
fixed, and what was consciously left open.

| File | What |
|---|---|
| [`QC_1.md`](QC_1.md), [`QC_2_AGENT.md`](QC_2_AGENT.md), [`QC_FINAL.md`](QC_FINAL.md) | QC passes over the UI and the agent, hosted and local. `QC_FINAL.md` carries the last hosted pass and the Lighthouse scores. |
| [`JUDGE_REVIEW_1.md`](JUDGE_REVIEW_1.md), [`JUDGE_REVIEW_2.md`](JUDGE_REVIEW_2.md), [`JUDGE_REVIEW_3.md`](JUDGE_REVIEW_3.md) | Adversarial self-reviews scored against the rubric, each followed by the fixes it triggered. |
| [`TRACKING.md`](TRACKING.md) | Append-only log of who changed what, per sprint. |
| [`img/`](img) | Screenshots used by the root README. |

Shared contracts live in [`../db/SCHEMA.md`](../db/SCHEMA.md) (agent-facing schema) and
`ARCHITECTURE.md`.
