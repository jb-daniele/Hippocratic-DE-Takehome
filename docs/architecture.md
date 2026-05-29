# StoryNest Architecture

This document is the detailed companion to the project [`README.md`](../README.md). It covers the multi-agent pipeline, judge contract, repair routing, safety touch points, and the encoding of bedtime-story principles into prompts and checks. The end-to-end pipeline diagram lives in [`StoryNest_DAG.pdf`](../StoryNest_DAG.pdf) at the repo root.

## 1. Classification

| Category id | Display name | Description |
|---|---|---|
| `general_bedtime_story` | General bedtime story | A calm, classic bedtime story for broad gentle requests. |
| `cozy_animal_story` | Cozy animal story | A snug story centered on friendly animals and comforting moments. |
| `gentle_adventure` | Gentle adventure | A low-stakes journey with discovery, courage, and a safe return. |
| `magical_bedtime_story` | Magical bedtime story | A soothing bedtime story with wonder, magic, or enchanted settings. |
| `friendship_and_feelings` | Friendship and feelings | A story about kindness, friendship, confidence, or naming feelings. |
| `silly_soft_story` | Silly soft story | A playful, funny story that stays gentle and bedtime-safe. |
| `calm_educational_story` | Calm educational story | A quiet story that introduces simple facts or concepts without becoming a lesson. |

Routing:

- Explicit `story_mode` is mapped through `STORY_MODE_TO_CATEGORY` in `story_engine/categories.py` and skips the Classifier (`classifier_skipped=True`).
- `auto_detect` first tries a deterministic inclusion/exclusion signal route in `classifier.py`; if that does not produce a clear winner, it invokes the Classifier tool with the catalog's inclusion/exclusion signals and few-shot examples.
- The Classifier tool path allows up to three attempts. Validation failures append a stricter retry prompt. After retries, the agent degrades instead of failing the run: it returns a parseable last response when possible, otherwise `general_bedtime_story` with `fallback=True` and `classifier_fallback_after_retries`.

The Classifier does not rewrite the request, plan the story, judge safety, generate content, invent categories, or score quality. Safety lives in the pre-request guard and Safety Judge, not in classification.

## 2. Length Handling

```python
SCENE_PLAN = {"scene_count": 4, "paragraphs_per_scene": 2}
```

Every story targets exactly 4 scenes × 2 paragraphs = 8 paragraphs. `_assert_target_paragraphs` runs at every pipeline stage (writer, post-stitch, polish, normalizer, final package). On drift it emits a `pipeline.paragraph_count_drift` trace event with `event_type="degraded"` and the pipeline reverts to the last structurally valid draft. Paragraph drift is treated as a soft signal, not a hard failure.

The Reader paginates by sentence-aware word budget (~120-word target, 180-word hard cap), so page counts vary by story length.

## 3. Agent Roles

Generative or planning agents (`story_engine/agents/`):

1. Classifier (`classifier.py`)
2. Character Designer (`planner.py::design_characters`)
3. Arc Planner (`planner.py::plan_arc`)
4. Scene Planner (`planner.py::plan_scenes`)
5. Scene Writer (`writer.py::write_draft`)
6. Scene Rewriter (`rewriter.py::rewrite_scene`) — per-scene repair driven by `validate_written_scene` hits and coherence fail codes
7. Scene Stitcher (`stitcher.py::stitch_scenes`) — bypassed when `check_scene_seams` passes; otherwise boundary-only edits
8. Polish (`polisher.py::polish`) — single post-judge revision; uses `polish_safety` or `polish_language` prompt
9. Title Writer (`title.py::write_title`) — runs last, after the final safety gate

Three boolean judges (`agents/judges.py`), run in parallel:

1. **Safety Judge** — pass/fail on the draft; re-run as a separate final safety gate after polish + normalizers.
2. **Coherence Judge** — scene-labeled fail codes (`request_drift`, `ownership_drift`, `continuity_break`, `weak_scene_progression`, `unresolved_central_problem`, `missing_resolution`, `missing_ending_image`, `must_avoid_violation`). When `split_scenes()` yields a valid 4-scene shape, labeled scene text is injected into the prompt; otherwise the judge falls back to flat `draft.body`. Failures route to per-scene rewrite, not polish. Parse exhaustion yields `verdict="unknown"` (does not halt the run).
3. **Language Judge** — pass/fail on read-aloud diction and surface form via structured failure codes. Parse exhaustion degrades to a synthetic pass (does not halt the run).

## 4. Judge Contract

Every judge returns a `JudgeReport` with:

```json
{
  "judge_name": "safety_judge",
  "verdict": "pass",
  "reason": null,
  "revision_guidance": null,
  "fail_codes": []
}
```

The contract is pass/fail only. Failing judges must provide `reason` and `revision_guidance`; passing judges keep both null. Coherence failures additionally carry structured `fail_codes` with per-scene `code` + `evidence`, which the pipeline uses to dispatch targeted scene rewrites instead of a whole-story polish. There are no numeric judge scores. After judges run, code paths never edit the story body directly — repair always goes through the Scene Rewriter or the Polish agent.

## 5. Repair Routing

After judges + deterministic checks run, `_route_failure_buckets` sorts post-eval failures into three buckets (`scene`, `polish_language`, `safety`). Only the **`scene`** bucket drives `_repair_scene_failures` (up to two loops). Polish activation is separate: `_polish_failures` collects failing judge reports (safety, language, but not coherence) plus synthetic language failures from deterministic `phrase_repetition` hits.

- **`scene`** — Coherence-judge `fail_codes` and deterministic `ending_image` failures. Routed to `_repair_scene_failures`, which calls `rewrite_scene` with `already_written_summary` / `upcoming_scene_summary` context.
- **`polish_language` (bucket)** — Deterministic `phrase_repetition` check results only (the check does not set `route` itself; the router assigns `polish_language` when the check name matches).
- **`safety` (bucket)** — Populated for tracing when the Safety Judge verdict is `fail`, but polish selection uses `_polish_failures`, not this bucket.

**Polish loop** (`MAX_POLISH_ITERATIONS = 3` in `pipeline/__init__.py`): each iteration runs `_polish_failures`, applies `polish` once per collected failure (safety → `polish_safety`, everything else → `polish_language`), re-runs `_evaluate_draft`, and stops when nothing remains to polish. If an iteration included a safety failure and the Safety Judge still fails afterward, the run halts with `failure_category="safety_fail"`. Paragraph drift during polish reverts to the last structurally valid draft.

**Fail-loud paths** (halt the run): pre-request guard block, Safety Judge tool exhaustion after retries (`judge_safety` raises `RunFailed`), safety still failing after a polish iteration that attempted safety repair, and the final Safety Judge gate after normalizers.

**Degraded paths** (continue with warnings/trace): planner agents return last parseable tool output or category-specific synthetic fallbacks after retries; `assemble_blueprint` pads missing scene cards; Scene Writer can synthesize from `must_show` beats; Language Judge parse exhaustion becomes pass; unapproved packages still return with warnings (including severe coherence: coherence fail + ≥3 high-severity deterministic failures → `approved=False`).

Approval-blocking checks (`APPROVAL_BLOCKING_CHECKS = ("phrase_repetition",)` plus `ending_image`) gate `JudgeDecision.approved` independently of judge verdicts.

## 6. Quality Principles → Implementation

| Principle | Prompt | Judge or code check |
|---|---|---|
| Low stakes | Scene Writer prompt requires gentle, low-stakes action. | Safety Judge and Coherence Judge flag unsafe or mismatched escalation. |
| Emotional arc | Arc Planner emits the spine; Scene Writer follows it scene by scene. | Coherence Judge checks that the story enacts the planned conflict and closure. |
| Vocabulary fit | Scene Writer prompt requires concrete, age-appropriate language. | Language Judge flags bedtime-incompatible diction on the draft body. |
| Concrete language | Scene Writer prompt asks for visible action and object interaction. | `validate_written_scene` enforces per-scene-card concrete action before stitching; failing scenes route to the Scene Rewriter. |
| Gentle pacing | Scene Planner produces 4 scenes × 2 paragraphs. | `_assert_target_paragraphs` traces drift and the pipeline reverts to the last structurally valid draft. |
| Coherent closure | Arc Planner emits `ending_image` and `central_problem`; the scene-4 card resolves them. | `check_ending_image` is an approval-blocking deterministic check; failing it routes scene 4 to the Rewriter. |
| Sensory warmth | Scene Writer prompt requires concrete sensory anchors per scene. | Coherence Judge fails on weak scene progression. |
| Repetition with purpose | Scene Stitcher seam repair removes accidental duplication; n-gram check flags repeated phrases. | `check_phrase_repetition` is approval-blocking; failures route to the language Polish pass. |
| Personalization | Scene Writer prompt requires every name in `main_characters` verbatim. | Coherence Judge fails missing personalization anchors. |
| Sleep landing | Scene Writer closing-scene instructions forbid new plot turns. | `check_ending_image` is the sleep-landing gate; severe coherence failure also blocks approval. |
| Safety | Shared safety headers shape all generation. | Pre-request guard, Safety Judge inside the judge fanout, and a final Safety Judge gate after polish/normalizers form a three-point safety layer. |

## 7. Safety: Three Touch Points

1. **Pre-request guard** — deterministic blocklist before any generation (`guardrails.pre_request_guard` in `run()` and again inside `understand()`); also re-run on feedback strings inside `revise_with_feedback`. A block raises `RunFailed`.
2. **Safety Judge inside the judge fanout** — runs in parallel with coherence and language judges. A **`fail` verdict** is routed into the polish loop (not an immediate halt). **`RunFailed`** is raised only if the Safety Judge tool call exhausts retries without a parseable response.
3. **Final Safety Judge gate** — re-run after polish and post-polish dialogue normalization (`_run_final_safety_gate`); a `fail` verdict here raises `RunFailed` before the Title Writer and packaging.

Safety is intentionally not hidden inside category classification. A story can be routed correctly and still be refused.

## 8. Persistence Layout

```text
stories/
  index.jsonl
  index.html
  <run_id>/
    story.json
    story.html
    llm-calls.jsonl
```

`story.json` contains request options, classification, blueprint, final package, and the flattened index entry. `stories/index.jsonl` drives retrieval and the saved-story sidebar. `stories/index.html` is a static library view.

## 9. Rated Example Candidates — Internal Details

When `record_user_rating` is called with `rating == 5`, `story_engine/persistence/candidate_examples.export_candidate_if_eligible` writes the run's planner artifacts to:

```text
data/prompt_example_candidates/{category_id}/{run_id}.json
```

Candidate payload top-level keys: `run_id`, `category_id`, `rating`, `created_at`, `story_title`, `request_text`, `story_spine`, `scene_cards`, `final_story_body`, `validation`, `promotion_status`. Validation flags: `category_id_present`, `story_spine_present`, `scene_cards_present`, `scene_count`, `final_story_body_present`, `candidate_saved`.

Re-rating semantics:

- `rating == 5` overwrites any existing `{run_id}.json` for that run.
- `rating < 5` deletes any prior candidate for that `run_id` across category subdirs.
- Empty or syntactically invalid `category_id` (anything not matching `^[a-z0-9_-]+$`) skips with a trace reason instead of writing.

Trace events: `prompt_example_candidate.saved`, `prompt_example_candidate.skipped` (with `reason`), `prompt_example_candidate.removed`, and `prompt_example_candidate.export_failed` (emitted exclusively by `record_user_rating`'s protective `try/except`, never by the exporter itself).

The exporter is not re-exported from `story_engine/persistence/__init__.py`, has no callers under `story_engine/prompts/` or any pipeline module, and the `data/prompt_example_candidates/` directory is gitignored. These are the structural guarantees that candidate examples never alter generation behavior.

## 10. Full Repo Tree

```text
.
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── docs/
│   └── architecture.md
├── data/
│   └── prompt_example_candidates/   # local-only, gitignored
├── logs/
├── stories/
├── tests/
├── storynest_app/
│   ├── __init__.py
│   ├── components.py
│   ├── state.py
│   └── screens/
│       ├── about.py
│       ├── completion.py
│       ├── cover.py
│       ├── error.py
│       ├── generating.py
│       ├── home.py
│       ├── library.py
│       ├── reader.py
│       ├── remix.py
│       ├── request.py
│       └── saved.py
└── story_engine/
    ├── __init__.py
    ├── categories.py
    ├── checks.py
    ├── config.py
    ├── errors.py
    ├── guardrails.py
    ├── schemas.py
    ├── trace.py
    ├── agents/
    │   ├── __init__.py
    │   ├── _common.py
    │   ├── classifier.py
    │   ├── judges.py
    │   ├── planner.py
    │   ├── polisher.py
    │   ├── rewriter.py
    │   ├── stitcher.py
    │   ├── stitcher_failure.py
    │   ├── title.py
    │   ├── tool_schemas.py
    │   └── writer.py
    ├── model_client/
    │   ├── __init__.py
    │   ├── call_log.py
    │   └── client.py
    ├── persistence/
    │   ├── __init__.py
    │   ├── candidate_examples.py
    │   ├── seeds.py
    │   └── store.py
    ├── pipeline/
    │   ├── __init__.py
    │   ├── _common.py
    │   ├── classify.py
    │   ├── judge.py
    │   ├── package.py
    │   ├── plan.py
    │   ├── polish.py
    │   └── write.py
    ├── prompts/
    │   ├── arc_planner.py
    │   ├── character_designer.py
    │   ├── classifier.py
    │   ├── coherence_judge.py
    │   ├── language_judge.py
    │   ├── output_schema_examples.py
    │   ├── paragraph_structures.py
    │   ├── polish_language.py
    │   ├── polish_safety.py
    │   ├── prompt_injection_helpers.py
    │   ├── safety_judge.py
    │   ├── scene_planner.py
    │   ├── scene_rewriter.py
    │   ├── scene_stitcher.py
    │   ├── scene_writer.py
    │   ├── shared.py
    │   └── title_writer.py
    └── text/
        ├── __init__.py
        ├── normalizers.py
        ├── reader.py
        ├── scene_split.py
        ├── summaries.py
        └── title_guard.py
```
