# StoryNest

## Overview

StoryNest is a local bedtime-story generator. A child's wish becomes a gentle, paginated read-aloud story through a structured multi-agent pipeline: the request is classified, a story spine and scene plan are drafted, each scene is written and repaired in place, judges check safety, coherence, and language, and the result is packaged for a paginated Reader.

It runs as a Streamlit app for end users and as a CLI for scripted use. Both share the same engine.

For the full pipeline diagram, see [`StoryNest_DAG.pdf`](StoryNest_DAG.pdf).

For the full judge contract, repair routing, and safety internals, see [`docs/architecture.md`](docs/architecture.md).

## Features

- Free-text story wish on the request screen
- Optional explicit story mode (`Auto-detect` plus seven curated modes) and optional main character name
- Generating screen with live trace-stage context while the pipeline runs
- Cover with title, category, character chips, and word/page counts
- Paginated Reader with sentence-aware word budgeting
- Completion screen where users can save a story and optionally record a 1–5 rating
- Story Shelf sidebar and a static `stories/index.html` library view
- Remix saved stories: pre-fills the saved blueprint and feeds an editable request back through generation
- Rated example candidates: 5-star saved stories are exported as local candidate prompt examples for later review
- CLI mode with the same engine, plus `--feedback` for a one-shot revision pass and `--debug` for trace + judge trail dumps

## Quick Start

Streamlit:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
streamlit run app.py
```

An `OPENAI_API_KEY` is required — the engine calls the OpenAI Chat Completions API at every generative stage. The key can also live in a `.env` file at the repo root (auto-loaded by `python-dotenv`).

CLI:

```bash
python main.py \
  --request "A bedtime story about a sleepy otter who lost his favorite rock" \
  --mode animal \
  --character Ollie
```

`--mode` accepts `auto_detect`, `classic`, `animal`, `gentle_adventure`, `magical`, `friendship`, `silly`, `educational`.

## How It Works

The Classifier routes the request into one of seven bedtime-story categories (or skips itself when the user picked an explicit mode). The Character Designer, Arc Planner, and Scene Planner produce a typed blueprint with a story spine and four scene cards. The Scene Writer drafts each scene against its card; per-scene validators send weak scenes back to the Scene Rewriter before stitching. Three judges — Safety, Coherence, Language — vote on the assembled draft in parallel, and failures route either to per-scene rewrites or to a polish pass. A final Safety Judge gate runs after polish and post-polish normalizers before the Title Writer finalizes the package.

Stories target exactly 4 scenes × 2 paragraphs (8 paragraphs total). Page counts vary because the Reader paginates by word budget.

## Quality and Safety

Quality is enforced in two layers: the prompts shape each agent's output (low-stakes action, concrete language, sensory anchors, named characters used verbatim, no new plot turns in the closing scene), and the judges check the assembled draft against those constraints. Coherence failures carry per-scene fail codes that drive targeted Scene Rewriter calls instead of a whole-story rewrite — repair is local where possible.

Safety has three touch points: a deterministic pre-request guard, the Safety Judge inside the parallel judge fanout, and a final Safety Judge gate after polish and normalizers. Safety is the only fail-loud path in the pipeline. Non-safety problems (paragraph drift, polish iterations not converging, stitcher edits straying outside scene boundaries, severe coherence failure after the repair budget is spent) degrade with structured trace events and warnings, and the pipeline prefers the latest structurally valid draft instead of halting.

The eight bedtime-story principles encoded in prompts and checks (low stakes, emotional arc, vocabulary fit, concrete language, gentle pacing, coherent closure, sensory warmth, sleep landing) are documented in [`docs/architecture.md`](docs/architecture.md#6-quality-principles--implementation).

## Persistence, Ratings, and Rated Example Candidates

Stories are persisted only when the user chooses to save them from the Completion screen. Each saved run gets a directory under `stories/<run_id>/` containing `story.json`, `story.html`, and the captured `llm-calls.jsonl`. A `stories/index.jsonl` drives the Story Shelf sidebar; `stories/index.html` is a static library view.

Ratings are optional metadata on saved stories. When a saved story receives a 5-star rating, StoryNest also exports the run's planner artifacts as a local candidate prompt example under:

```text
data/prompt_example_candidates/{category_id}/{run_id}.json
```

Each candidate captures the category, original request, final story body, StorySpine, SceneCards, and a small validation block. The directory is gitignored — candidates stay local to each user or reviewer, so anyone running StoryNest can build a private collection of the story shapes they preferred most. They are review material for later curation, not runtime input to generation.

## Technical Highlights

- Structured multi-agent generation with explicit roles (planner, writer, rewriter, stitcher, polish, title) and three boolean judges
- Typed intermediate artifacts (`StoryBlueprint`, `StorySpine`, `SceneCard`, `DraftStory`, `FinalStoryPackage`, `JudgeReport`)
- Scene-level repair driven by per-scene fail codes — local rewrites instead of whole-story regeneration
- Tool-call judges with a strict pass/fail contract; revision guidance is structured, not freeform
- Per-run trace events and complete LLM call log persisted alongside each saved story
- Local rating-derived candidate examples for offline review and future curation
- Soft-fail design: safety raises, everything else degrades to warnings and the last structurally valid draft

## Future Work

StoryNest can export saved stories rated 5 stars as local rated example candidates. Each candidate captures the story's category, original request, final story body, StorySpine, SceneCards, and lightweight validation details. These candidate files are stored locally under `data/prompt_example_candidates/`, allowing each user or reviewer to build a private collection of examples that reflect the kinds of stories they preferred most.

With more implementation time, these rated candidates could become the foundation for a curated example-improvement workflow. A reviewer could inspect high-rated candidates, compare their planner artifacts against quality checks, and promote the strongest ones into category-specific prompt example libraries. This would let StoryNest improve from real user feedback while keeping example changes intentional, reviewable, and reversible.

Longer term, this system could support per-category example collections, local personalization, A/B testing of promoted examples, and analytics showing which example sets produce the most readable stories. The goal would be a safe feedback loop where user ratings help identify strong story patterns, and curated promotion turns those patterns into better future generations.

## Repo Layout

```text
storynest_app/              Streamlit UI screens and shared components
story_engine/agents/        LLM agents and judges
story_engine/prompts/       Prompt templates and shared headers
story_engine/pipeline/      Orchestration: classify, plan, write, judge, polish, package
story_engine/persistence/   Saved stories, ratings, and rated example candidates
story_engine/model_client/  OpenAI client and per-run LLM call log
stories/                    Local saved-story outputs (per-run dir + index)
data/prompt_example_candidates/   Local-only candidate examples (gitignored)
logs/                       Per-run trace and LLM-call JSONL
tests/                      Unit tests (run with `python -m unittest discover tests`)
docs/architecture.md        Detailed pipeline, judge, and repair-routing reference
```
