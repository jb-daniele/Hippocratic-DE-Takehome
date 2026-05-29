from __future__ import annotations

import json
from typing import Any

from story_engine.prompts.paragraph_structures import character_cards_payload

_PASSING_OUTPUT = """{
  "passed": true,
  "fail_codes": []
}"""

_FAILING_OUTPUT = """{
  "passed": false,
  "fail_codes": [
    {
      "code": "request_drift",
      "evidence": "verbatim quote from story",
      "scene_index": null
    }
  ]
}"""

_FAILING_INPUT = """{
  "request": "Write a bedtime story about a child finding a missing red button with help from a mouse.",
  "story_spine": {
    "central_problem": "The red button is missing before bedtime.",
    "resolution": "The child and Mouse find the red button under the bed and sew it back on.",
    "ending_image": "The child sleeps while the red button sits neatly on the pajama sleeve.",
    "must_avoid": ["owl helper", "large adventure"]
  }
}"""

_FAILING_STORY_EXCERPT = """The child looked for the red button, then looked again in the same drawer. An owl flew in and pointed toward a shiny key. At bedtime, the child felt happy because everything was finally okay."""

_FAILING_EXAMPLE_OUTPUT = """{
  "passed": false,
  "fail_codes": [
    {
      "code": "weak_scene_progression",
      "evidence": "looked for the red button, then looked again in the same drawer",
      "scene_index": null
    },
    {
      "code": "request_drift",
      "evidence": "An owl flew in and pointed toward a shiny key",
      "scene_index": null
    },
    {
      "code": "missing_resolution",
      "evidence": "pointed toward a shiny key",
      "scene_index": null
    },
    {
      "code": "missing_ending_image",
      "evidence": "felt happy because everything was finally okay",
      "scene_index": null
    },
    {
      "code": "must_avoid_violation",
      "evidence": "An owl flew in",
      "scene_index": null
    }
  ]
}"""


def _plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def build_prompt(draft: Any, blueprint: Any, classification: Any, request: str, *, scenes: list[str] | None = None) -> str:
    cast = character_cards_payload(blueprint.character_cards)
    passing_output = _PASSING_OUTPUT
    failing_output = _FAILING_OUTPUT
    failing_input = _FAILING_INPUT
    failing_excerpt = _FAILING_STORY_EXCERPT
    failing_example_output = _FAILING_EXAMPLE_OUTPUT
    story_body = draft.body
    scene_count = blueprint.scene_plan["scene_count"]
    if (
        isinstance(scenes, list)
        and len(scenes) == scene_count
        and all(str(scene).strip() for scene in scenes)
    ):
        story_body = "\n\n".join(f"Scene {index + 1}:\n{scene}" for index, scene in enumerate(scenes))
    return f"""# Role

You are the StoryNest Coherence Judge.

# Task

Judge only clear, visible story-mechanics failures.

Do not rewrite the story.  
Do not judge prose style.  
Do not judge local SceneCard compliance.  
Do not judge language polish issues.

---

# Inputs

- request:
```text
{request}
```

- story_spine:
```json
{json.dumps(_plain(blueprint.story_spine), ensure_ascii=False, indent=2)}
```

- cast:
```json
{json.dumps(cast, ensure_ascii=False, indent=2)}
```

# Story Body

```text
{story_body}
```

---

# Judgment Priority

The user request is the highest source of truth.

If `request` and `story_spine` conflict, judge against `request`.

The story must preserve the requested character, object, helper, place, activity, mechanism, route, direction, and outcome.

Fail if the story replaces the requested mechanism with a different mechanism, even if the replacement makes a pleasant story.

---

# Checks

Fail only for clear, visible story-mechanics failures where:

- the story drops, replaces, reverses, or changes a requested character, object, helper, place, activity, mechanism, route, direction, or outcome
- a decorative helper, clue, object, magical detail, or mood detail replaces or competes with the requested mechanism
- a pretend, imagined, guessed, or described thing becomes real when the request does not make it real
- characters, objects, ownership, places, timing, scene order, or unrelated inserted content become confusing or inconsistent
- two or more scenes repeat the same main problem, action, clue, search, helper action, choice, object beat, or solved state without adding a real new step
- the central problem is only emotionally settled, not visibly changed
- the story does not show `story_spine.resolution`, or resolves through a different mechanism than the request requires
- the final scene does not show a concrete settled image with physical proof that the problem is solved
- the ending uses happiness, peace, warmth, togetherness, wonder, or comfort as the main proof of resolution instead of showing the resolved object, place, routine, route, relationship, or situation on-page
- the story includes anything from `story_spine.must_avoid`

Do not fail for:

- plain wording
- repeated mood words
- stiff dialogue
- quote-formatting issues
- repeated sentence openings
- prose that could be more polished but still preserves the story mechanics

Language quality belongs to the Language Judge.

Use only these codes:

```text
request_drift
ownership_drift
continuity_break
weak_scene_progression
unresolved_central_problem
missing_resolution
missing_ending_image
must_avoid_violation
```

---

# Code Meanings

- `request_drift`: the story changes, replaces, reverses, or weakens the user-requested premise, mechanism, direction, object, helper, place, activity, route, or outcome.
- `ownership_drift`: a character uses, owns, carries, fixes, finds, or decides something that belongs to another character without clear story support.
- `continuity_break`: characters, objects, places, timing, scene order, or inserted content contradict each other.
- `weak_scene_progression`: scenes repeat the same problem, action, clue, helper move, choice, solved state, or success without a meaningful new step.
- `unresolved_central_problem`: the central problem remains visibly unsettled, or is settled only by feelings, mood, reassurance, or summary.
- `missing_resolution`: the story does not show the concrete resolving action from `story_spine.resolution`, or uses a different solving mechanism.
- `missing_ending_image`: the final scene does not show physical proof of settlement from `story_spine.ending_image`.
- `must_avoid_violation`: the story includes something listed in `story_spine.must_avoid`.

---

# Scene Index

Use the labeled Scene 1-4 sections in `story_body` when they are present.

- If the evidence quote appears inside one labeled scene, use that scene number.
- Use `scene_index` for scene-level failures.
- Use `scene_index: null` only for failures that affect the whole story or cannot be localized to one scene.
- Do not use `scene_index: null` just because a failure is serious.
- Ending failures should usually use Scene 4 unless the failure is truly whole-story.

---

# Evidence

- Each failure needs a short verbatim quote from the story.
- Evidence must be 120 characters or fewer.
- Choose quotes that make the failure easy for a repair agent to find.
- If the failure is about something missing, quote the closest place where the story incorrectly skips, replaces, or summarizes it.

---

# Output

Return JSON only.

Passing shape:

```json
{passing_output}
```

Failing shape:

```json
{failing_output}
```

---

# Failure Example

Use this example only for judgment logic.

Input:

```json
{failing_input}
```

Story excerpt:

```text
{failing_excerpt}
```

Output:

```json
{failing_example_output}
```

---

# Final Check

Before returning, make sure:

- the user request outranks the StorySpine when they conflict
- requested mechanisms were not replaced by decorative helpers, clues, magic, or mood
- repeated scenes are failed as `weak_scene_progression`
- emotional comfort alone is not accepted as resolution
- the final scene shows physical proof of settlement
- `scene_index` uses labeled scene sections when available
- every failure has a short quote the repair agent can use

Return valid JSON only."""
