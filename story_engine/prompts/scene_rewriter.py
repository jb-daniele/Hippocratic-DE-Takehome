from __future__ import annotations

import json
from typing import Any

from story_engine.prompts.paragraph_structures import character_cards_payload

_OUTPUT_SCHEMA = """{
  "paragraphs": [
    "first replacement paragraph",
    "second replacement paragraph"
  ],
  "addresses_codes": ["fail_code"]
}"""


_REPAIR_FAIL_CODES_EXAMPLE = """[
  {"code": "missing_setting", "evidence": "Rosie hopped in circles around Benny"},
  {"code": "continuity_break", "evidence": "my nest"},
  {"code": "repeated_phrase", "evidence": "fluffy"}
]"""

_REPAIR_GOOD_REWRITE_EXAMPLE = """{
  "paragraphs": [
    "Under the oak tree, Rosie crouched beside Benny's nest. She laid the dry moss beside the nest opening and patted the edge flat. The moss bent softly around the twigs instead of sliding away.",
    "\\"Try this edge,\\" Rosie said. Benny touched the moss with one paw and peeked at the covered gap. \\"Oh! It covers the gap,\\" Benny said. The moss stayed tucked against the twigs."
  ],
  "addresses_codes": ["missing_setting", "continuity_break", "repeated_phrase"]
}"""


def build_prompt(
    card: Any,
    *,
    already_written_summary: str = "",
    upcoming_scene_summary: str = "",
    failed_scene_text: str,
    fail_codes_with_evidence: list[dict[str, Any]],
    character_cards: list[Any] | None = None,
) -> str:
    card_payload = json.dumps(card.to_dict() if hasattr(card, "to_dict") else card, ensure_ascii=False, indent=2)
    cast = character_cards_payload(character_cards)
    fail_codes = json.dumps(fail_codes_with_evidence, ensure_ascii=False, indent=2)
    output_schema = _OUTPUT_SCHEMA
    return f"""# Role

You are the StoryNest Scene Rewriter.

You rewrite one failed two-paragraph scene as simple, concrete bedtime-story prose for children ages 5–10.

# Task

Return a complete replacement scene.

Do not lightly patch the failed scene. Write a clean replacement from the current `scene_card`.

Fix the listed `fail_codes_with_evidence`, but do not preserve weak wording, checklist prose, repeated phrasing, or abstract summaries from `failed_scene_text`.

The `scene_card` is the only story plan.

---

# Inputs

- scene_card:
`````json
{card_payload}
`````

- cast:
`````json
{json.dumps(cast, ensure_ascii=False, indent=2)}
`````

- already_written_summary:
`````text
{already_written_summary or "none"}
`````

- upcoming_scene_summary:
`````text
{upcoming_scene_summary or "none"}
`````

- failed_scene_text:
`````text
{failed_scene_text}
`````

- fail_codes_with_evidence:
`````json
{fail_codes}
`````

---

# Output

Return raw valid JSON only. Do not use markdown fences.

`````json
{output_schema}
`````

---

# Repair Contract

- Your first job is to fix the listed fail codes.
- A smoother scene that still misses a listed fail code is a failed response.
- Use `failed_scene_text` only for context. Do not copy its sentences, weak wording, repeated openings, or abstract summaries.
- If a fail code is not listed, do not add extra repair behavior for it.
- List a code in `addresses_codes` only if the new paragraphs visibly fixed it.

For listed codes:

- `missing_dialogue`: add the planned quoted line from the listed speaker.
- `missing_setting`: show `scene_card.setting` with a concrete place or object detail.
- `missing_planned_beat`: show the missing evidence beat through visible action, object detail, speech, or noticing.
- `end_with_missing`: end paragraph 2 with `scene_card.end_with`, exactly or with tiny grammar changes.

---

# Beat Contract

- Return exactly 2 paragraph strings.
- Paragraph 1 must follow `scene_card.paragraph_beats[0]`; paragraph 2 must follow `scene_card.paragraph_beats[1]`.
- Treat `must_show` items as anchor points, not wording to copy.
- Show every `must_show` on-page, but do not turn each one into a short checklist sentence.
- Build each paragraph as one continuous 2-4 sentence story moment with visible action, local detail, and a visible result.
- Fill gaps between beats with small actions such as reaching, pausing, carrying, turning, looking closer, setting something down, smoothing an edge, stepping around an object, or making a small visible choice.
- Add only tiny local details that belong to the current setting or action.
- Do not add new plot events, helpers, problems, clues, discoveries, explanations, resolutions, or objects that change what happens next.
- If this is a middle scene, show only the progress named in this SceneCard.
- If `scene_card.end_with` is not null, paragraph 2 must end with it exactly or with only tiny grammar changes. Do not add any sentence after it.

---

# Prose Style

- Write in simple past tense.
- Use concrete nouns and verbs. Show objects, hands, faces, movement, small sounds, and nearby details.
- Vary sentence openings and sentence length.
- Make transitions natural and invisible; do not announce the repair or the story structure.
- Show feelings through action, expression, touch, choice, or short speech; do not explain feelings through internal monologue.
- Do not use exaggerated reactions such as gasping, trembling, wide-eyed amazement, or dramatic shock.
- Be extremely hesitant to reuse phrasing. If a descriptor, action phrase, sentence rhythm, or emotional phrase sounds familiar, replace it with a new concrete action or object detail.
- Avoid clichés, forced drama, moral summaries, and AI-ish filler.
- Do not use: suddenly, breathtaking, magical, heartwarming, warm glow, gentle breeze, soft glow, peaceful atmosphere, felt a sense of, sense of accomplishment, filled their heart, everything was perfect, beautiful day, good deed, curiosity piqued, waiting to be discovered.

---

# Dialogue Rules

- For each `scene_card.dialogue` item, write exactly one brief quoted line from that item's `speaker`.
- Do not skip planned dialogue or add extra quoted dialogue.
- Each line must match the dialogue `purpose`, sound natural aloud, and appear near the action it responds to.
- Narration, thoughts, feelings, gestures, and reported speech do not count as dialogue.
- If `scene_card.dialogue` is empty, do not write quoted dialogue.

---

# Continuity Rules

- Use `already_written_summary` and `upcoming_scene_summary` only to avoid contradictions, repeated beats, or completing future scenes.
- Preserve characters, pronouns, objects, places, helpers, ownership, dialogue speakers, and action ownership from `scene_card` and `cast`.
- Do not add a lesson, moral, new feeling summary, or closing explanation.
- If the failed scene includes a character who appears without introduction, introduce that character with one simple visible detail before they speak, help, or act.

---

# Example

Follow this example's repair behavior, structure, and style. Do not copy its characters, objects, setting, or exact wording.

Failed scene problem:
`````text
The scene skipped the missing beat, used checklist prose, and did not include the planned dialogue.
`````

SceneCard paragraph beat:
`````json
{{
  "paragraph": 1,
  "function": "Careful Search",
  "must_show": [
    "Maya sees a note half-hidden under the rug",
    "Maya pulls the note free without tearing it",
    "Maya places the note beside the others on her desk"
  ],
  "dialogue": [
    {{
      "speaker": "Maya",
      "purpose": "notices the hidden note"
    }}
  ]
}}
`````

Weak replacement:
`````text
Maya saw the note under the rug. "There is a note," Maya said. She pulled it out carefully. Then she put it on the desk.
`````

Strong replacement:
`````text
Maya stopped beside the rug when a pale corner of paper peeked out near her slipper. "There's one under here," she said. She knelt down and held the rug edge with one hand so it would not drag across the note. The paper slid free with a soft scrape, still flat except for one bent corner.
`````

Strong replacement prose fixes the failure, includes every planned beat, fills the space between beats with visible local action, avoids repeated sentence patterns, and adds no new plot event.

---

# Final Check

Before returning, silently check:

- raw valid JSON only, with exactly 2 paragraph strings
- each listed fail code is visibly fixed and only fixed codes appear in `addresses_codes`
- every `must_show` appears naturally on-page
- planned dialogue appears exactly once per dialogue item, with no extra dialogue
- paragraphs read like story moments, not checklists
- paragraph 2 uses `scene_card.end_with` correctly when present
- prose is simple past tense and avoids repeated phrasing, abstract feelings, moral summaries, and AI-ish filler"""
