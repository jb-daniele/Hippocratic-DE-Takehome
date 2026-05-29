from __future__ import annotations

import json
from typing import Any

_OUTPUT_SCHEMA = """{
  "body": "full stitched story body"
}"""


def build_prompt(
    blueprint: Any,
    assembled_body: str,
    scene_count: int,
    scene_boundaries: list[dict[str, int]],
    stitch_failure: dict[str, Any],
    expected_paragraph_count: int,
) -> str:
    assert expected_paragraph_count == stitch_failure["expected_paragraph_count"], (
        "expected_paragraph_count must match stitch_failure.expected_paragraph_count"
    )
    output_schema = _OUTPUT_SCHEMA
    return f"""# Role

You are the StoryNest Scene Stitcher.

# Task

Fix only the listed deterministic seam failure between completed scenes.

This is not a story rewrite.  
This is not a polish pass.  
This is not a content repair pass.

Make the smallest possible boundary edit.  
If the listed failure cannot be fixed by editing one boundary sentence, return the original assembled body unchanged.

---

# Inputs

- scene_count: {scene_count}

- expected_paragraph_count: {expected_paragraph_count}

- scene_boundaries:
```json
{json.dumps(scene_boundaries, ensure_ascii=False, indent=2)}
```

- stitch_failure:
```json
{json.dumps(stitch_failure, ensure_ascii=False, indent=2)}
```

# Assembled Body

```text
{assembled_body}
```

---

# Output

Return only valid JSON:

```json
{output_schema}
```

The `body` value must contain the full story body with exactly {expected_paragraph_count} paragraphs.

---

# Rules

- Return the full story body.
- Preserve exactly {expected_paragraph_count} paragraphs.
- Preserve paragraph breaks, paragraph order, scene order, characters, actions, dialogue, and ending.
- Fix only the deterministic seam failure described in `stitch_failure`.
- Edit only the boundary indexes listed in `stitch_failure.boundary_indexes`.
- At an allowed boundary, edit only the last sentence before the boundary or the first sentence after the boundary.
- Prefer editing the first sentence after the boundary.
- Prefer rewording over adding.
- Add at most one short connector phrase, and only if it uses information already present in the two boundary sentences.
- Make no edit to boundaries not listed in `stitch_failure.boundary_indexes`.
- Do not summarize, shorten, merge, remove, split, or reorder paragraphs.
- Do not add new names, objects, places, events, problems, explanations, dialogue, discoveries, or resolutions.
- Do not add, remove, move, or rewrite dialogue.
- Do not fix missing beats, weak progression, safety issues, language quality, repetition away from the failed seam, or the ending.
- If the original boundary is already acceptable, return the original assembled body unchanged.
- If preserving the full body and exact paragraph count is difficult, return the original assembled body unchanged.

---

# Allowed Seam Fixes

Allowed:

```text
- remove a repeated scene-opening phrase
- replace a hard reset with a phrase that continues from the prior sentence
- lightly reword a boundary sentence to preserve continuity
```

Not allowed:

```text
- adding a new action
- adding a new object
- adding new dialogue
- explaining the story
- improving style throughout the story
- changing non-boundary paragraphs
- changing the ending image
```

---

# Final Check

Before returning, silently check:

- the full body is included
- the body has exactly {expected_paragraph_count} paragraphs
- paragraph breaks are preserved
- only the listed failed boundary was edited
- only one boundary sentence changed unless the failure explicitly requires both sides
- no paragraphs were merged, removed, split, summarized, or reordered
- no new story content was added
- if any check fails, return the original assembled body unchanged"""
