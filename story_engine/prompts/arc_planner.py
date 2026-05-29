from __future__ import annotations

import json
from typing import Any

from story_engine.prompts.output_schema_examples import story_spine_example_for
from story_engine.prompts.paragraph_structures import character_cards_payload, scene_structure_prompt_payload

#For prompt engineering reference only
_OUTPUT_SCHEMA = """{
  "story_premise": "Specific one-sentence summary: protagonist, visible problem, and concrete resolution path.",
  "protagonist_name": "Name from cast who experiences or carries the central problem.",
  "setting": "One concrete place where the main story action happens.",
  "central_problem": "Small visible problem a child can understand.",
  "resolution": "Concrete action that visibly solves or settles the problem before the ending.",
  "ending_image": "Quiet final image with named character, settled object/place/situation, and proof the problem is solved.",
  "scene_count": 4,
  "scene_steps": [
    "Concrete scene 1 event aligned with scene_structure.scenes[0].",
    "Concrete scene 2 event aligned with scene_structure.scenes[1].",
    "Concrete scene 3 event aligned with scene_structure.scenes[2].",
    "Concrete scene 4 event aligned with scene_structure.scenes[3]."
  ],
  "must_avoid": ["Concrete exclusion for this story."]
}"""


def build_prompt(classification: Any, scene_plan: dict[str, int], character_cards: list[Any] | None = None) -> str:
    category_id = classification.category_id
    scene_structure = scene_structure_prompt_payload(category_id)
    cast = character_cards_payload(character_cards)
    scene_count = int(scene_plan["scene_count"])
    story_spine_example = story_spine_example_for(category_id)
    must_avoid_hint = (
        '- must_avoid must include "moralizing ending".'
        if category_id == "friendship_and_feelings"
        else "- must_avoid should name concrete bedtime-safety exclusions."
    )
    return f"""# Role

You are the StoryNest Arc Planner.

# Task

Create a concrete StorySpine for a four-scene bedtime story.

The StorySpine must preserve the user request and give a visible path from one small problem to one concrete resolution.

Each `scene_step` must contain two visible beats joined by “then.”

---

# Inputs

- category_id: {category_id}

- scene_structure:
````json
{scene_structure}
````

- request:
````text
{classification.request_text}
````

- scene_count: {scene_count}

- cast:
````json
{json.dumps(cast, ensure_ascii=False)}
````

---

# Output

Use the required tool. Return only the StorySpine.

---

# Core Rules

- Use the request as the source of truth.
- Preserve requested characters, objects, places, activities, mechanisms, direction, and outcome unless unsafe.
- Use only the provided cast for named characters.
- `protagonist_name` must exactly match one cast member name.
- Do not add a helper when the requested object, clue, place, or action can guide or solve the story.
- Do not turn pretend, imagined, guessed, or described things into real events unless the request says they are real.
- Keep the story bedtime-safe: no danger, villains, punishment, chase scenes, scary mystery, rescue plots, or high stakes.
- {must_avoid_hint}

---

# StorySpine Rules

# StorySpine Rules

- `setting` must be one simple concrete place.
- `central_problem` must name a visible small problem: something missing, stuck, unclear, unfinished, out of place, or not ready.
- `resolution` must name who does what to which object, place, routine, clue, or activity.
- `resolution` must use the request's solving mechanism when the request gives one.
- `ending_image` must show the solved object, place, routine, or relationship in its final visible state.
- Every StorySpine field must be useful to the Scene Planner. Prefer specific object positions, visible changes, and concrete actions over feelings, mood, scenery, or summaries.
- Do not use feelings, mood, happiness, togetherness, a lesson, or a moral as the problem, resolution, or ending_image.

---

# Scene Step Rules

- Return exactly {scene_count} scene_steps.
- Follow `scene_structure.scenes` in order.
- Each scene_step must be one full planning sentence with two visible beats joined by “then.”
- Each beat must name who acts, what they touch, move, notice, or say, where it happens, and what visibly changes.
- Each scene_step must show a visible cause-and-effect change: an object moves, a clue is found, a route becomes clearer, a choice is made, a task advances, or the problem becomes closer to solved.
- Each scene_step should include concrete story material the Scene Planner can expand: a place, an object, a character action, and a visible result.
- Scene 1 sets up the problem.
- Scene 2 makes progress without solving it.
- Scene 3 solves the problem.
- Scene 4 shows the settled physical ending image.
- Do not repeat the same problem, clue, action, solved state, or generic happiness across scenes.
- Avoid scene_steps that only say the character tries, searches, continues, learns, feels, enjoys, or gets ready; name the exact action and what changes on-page.

---

# Repair Rules

If repairing a schema failure, make the smallest change needed and keep already-concrete fields.

---

# Example

Use this example for output shape and specificity only. Do not copy its names, objects, route, helper, setting, or beats.

````json
{story_spine_example}
````

---

# Final Check

Before returning, make sure:

- the request mechanism and outcome are preserved
- the problem, resolution, and ending image are physical and visible
- each scene_step has exactly two concrete beats joined by “then”
- Scene 1 sets up, Scene 2 progresses, Scene 3 solves, Scene 4 settles
- no field relies on happiness, peace, warmth, pride, scenery, a lesson, or a moral"""
