from __future__ import annotations

import json
from typing import Any

#from story_engine.prompts.output_schema_examples import scene_card_example_for
from story_engine.prompts.paragraph_structures import character_cards_payload, paragraph_structure_prompt_payload

# For reference when prompt engineering, this variable is now longer injected in the prompt due to tool calling.
_OUTPUT_SCHEMA = """{
  "scene_cards": [
    {
      "scene": 1,
      "paragraphs": [1, 2],
      "setting": "specific place for this scene",
      "scene_change": "what visibly changes by the end of this scene",
      "paragraph_beats": [
        {
          "paragraph": 1,
          "function": "paragraph function name",
          "must_show": [
            "visible action, object detail, or child-clear story beat",
            "visible action, object detail, or child-clear story beat"
          ]
        },
        {
          "paragraph": 2,
          "function": "paragraph function name",
          "must_show": [
            "visible action, object detail, or child-clear story beat",
            "visible action, object detail, or child-clear story beat"
          ]
        }
      ],
      "dialogue": [
        {
          "speaker": "cast member name",
          "purpose": "what the line should do, not exact wording"
        }
      ],
      "end_with": null
    }
  ]
}"""

_WEAK_BEAT_EXAMPLE = """{
  "paragraph": 2,
  "function": "Small Practical Problem",
  "must_show": [
    "Maya helps with the room",
    "the plant needs care"
  ]
}"""

_STRONG_BEAT_EXAMPLE = """{
  "paragraph": 2,
  "function": "Small Practical Problem",
  "must_show": [
    "Maya sets the watering can on the windowsill beside the plant",
    "one leaf hangs over the pot edge and the soil is pale",
    "Maya points to the dry soil and calls Grandma over"
  ]
}"""

    #scene_cards_example = scene_card_example_for(category_id)
    #weak_beat_example = _WEAK_BEAT_EXAMPLE
    #strong_beat_example = _STRONG_BEAT_EXAMPLE

def _plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def build_prompt(spine: Any, character_cards: list[Any], classification: Any) -> str:
    category_id = classification.category_id
    character_names = [
        name
        for card in character_cards
        for name in [getattr(card, "name", None) if not isinstance(card, dict) else card.get("name")]
        if name
    ]
    valid_speakers = json.dumps(character_names, ensure_ascii=False)
    cast = character_cards_payload(character_cards)
    paragraph_structure = paragraph_structure_prompt_payload(category_id)

    return f"""# Role

You are the StoryNest Scene Planner.

# Task

Turn the StorySpine into 4 executable SceneCards.

Each SceneCard covers 2 story paragraphs. Each paragraph needs concrete `must_show` beats the Writer can show directly on-page.

Use `paragraph_structure` to shape the four-scene progression.

---

# Inputs

- category_id: {classification.category_id}

- request:
````text
{classification.request_text}
````

- story_spine:
````json
{json.dumps(_plain(spine), ensure_ascii=False, indent=2)}
````

- paragraph_structure:
````json
{paragraph_structure}
````

- cast:
````json
{json.dumps(cast, ensure_ascii=False, indent=2)}
````

---

# Output

Use the required tool. Return only the `scene_cards` array.

---

# Planning Rules

- Use `story_spine` as the source of truth.
- Preserve the requested character, object, place, activity, direction, mechanism, resolution, and ending.
- Do not include anything from `story_spine.must_avoid`.
- Use `paragraph_structure.scenes` for scene order, paragraph numbers, paragraph functions, and scene purpose.
- Split each matching `story_spine.scene_steps` item into two paragraph beats.
- Use the first listed paragraph function for the first beat and the second listed paragraph function for the second beat.
- If characters imagine, pretend, guess, or describe something, keep it as imagining, pretending, guessing, pointing, arranging, drawing, or describing. Do not make it real unless the request says it is real.

---

# Scene Progression

- Scene 1 shows the setup and makes `story_spine.central_problem` visible.
- Scene 2 shows progress, a careful attempt, a test, a notice, or one next step. Do not solve the problem yet.
- Scene 3 includes the concrete solving action from `story_spine.resolution`.
- Scene 4 shows the settled behavior and final physical image from `story_spine.ending_image`.
- Scene 3 solves; Scene 4 settles.
- Each scene must make a different thing newly true.
- Do not repeat the same problem, clue, action, solved state, or generic happiness across scenes.

---

# Field Rules

- `setting` must be a simple concrete location label.
- `scene_change` must name what visibly changed by the end of the scene.
- Each `must_show` must be a visible beat with character + object/place + action or visible state change.
- `must_show` beats should give the Writer concrete material: objects, positions, hands, faces, movement, small sounds, or visible reactions.
- Do not use mood, feeling, effort, success, atmosphere, or a lesson as a `must_show`, `scene_change`, dialogue purpose, or `end_with`.
- Avoid weak beats such as “helps,” “continues,” “tries hard,” “gets ready,” “feels better,” “learns,” “understands,” “looks happy,” or “checks everything.”
- Set `end_with` to `null` for Scenes 1, 2, and 3.
- Scene 4 `end_with` must match `story_spine.ending_image` and show a physical final image: an object in place, a body at rest, a finished arrangement, or the solved situation on-page.
- Do not introduce a new main activity, helper, problem, solution, clue, or object in Scene 4.

---

# Dialogue Rules

# Dialogue Rules

- Dialogue speakers must be exactly one of {valid_speakers}.
- Most scenes should have zero or one dialogue item. Use two only for a brief useful exchange.
- Add dialogue only when a character needs to say something useful aloud: name the problem, ask what to try, offer one next step, notice what changed, or thank someone.
- Dialogue purposes must be speakable functions, not actions, feelings, summaries, or exact wording.
- A good purpose should be easy to turn into one short quoted line.
- Bad purposes: “looks at the desk,” “finds the note,” “checks the room,” “climbs into bed,” “feels happy,” “enjoys the peaceful scene,” “sits with contentment,” “shares a quiet moment.”
- Good purposes: “names what is missing,” “asks where to look next,” “offers one next step,” “notices the object is back in place,” “thanks the helper.”

---

# Must_Show Example

Use this only for beat specificity. Do not copy its names, objects, setting, or actions.

Weak:
````json
[
  "Nora notices the plant needs help",
  "the plant looks sad",
  "Grandma helps Nora with the plant",
  "Nora learns what the plant needs"
]
````

Strong:
````json
[
  "Nora stands beside Grandma's bedroom windowsill and notices the plant on the table",
  "one limp green stem bends toward the curtain and two leaves hang over the pot edge",
  "Grandma notices and taps the dry soil near the plant stem, telling Nora to water the plant",
  "Nora lifts the small watering can from the windowsill and holds it over the plant pot"
]
````

Strong beats use character, object, place, visible action, and visible state change. They give the Writer concrete material without writing prose.

---

# Final Check

Before returning, make sure:

- exactly 4 SceneCards
- paragraph numbers and functions match `paragraph_structure`
- Scene 2 does not solve the central problem
- Scene 3 contains the concrete solving action from `story_spine.resolution`
- Scene 4 has a concrete `end_with` matching `story_spine.ending_image`
- every `must_show` is concrete, visible, and writer-ready
- dialogue speakers are exactly from {valid_speakers}
- each dialogue purpose can become one short natural quoted line
- no dialogue purpose is an action, mood, feeling, summary, or exact line
- no scene uses happiness, peace, warmth, pride, togetherness, or a lesson as ending_image
"""
