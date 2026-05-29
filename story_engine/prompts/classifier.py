from __future__ import annotations

import json
from typing import Any

_OUTPUT_SCHEMA = """{
  "category_id": "one listed category id",
  "confidence": "high | medium | low",
  "rationale": "short classification rationale",
  "matched_signals": ["signal"],
  "fallback": false
}"""


def _category_block(category: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- id: {category['id']}",
            f"  display_name: {category['display_name']}",
            f"  description: {category['description']}",
            f"  inclusion_signals: {', '.join(category['inclusion_signals'])}",
            f"  exclusion_signals: {', '.join(category['exclusion_signals'])}",
        ]
    )


def _pooled_examples(categories: list[dict[str, Any]]) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    for category in categories:
        for example in category.get("classifier_examples", [])[:3]:
            examples.append(
                {
                    "request": example["request"],
                    "category": example["category"],
                    "reason": example["reason"],
                }
            )
            if len(examples) >= 15:
                return examples
    return examples


def build_prompt(request: str, story_mode_hint: str, categories: list[dict[str, Any]]) -> str:
    category_list = "\n".join(_category_block(category) for category in categories)
    category_ids = [category["id"] for category in categories]
    examples = json.dumps(_pooled_examples(categories), indent=2, sort_keys=True)
    return f"""# Role

You are the StoryNest Request Classifier.

# Task

Choose exactly one `category_id` from the allowed list.

Classify only. Do not plan or write the story.

---

# Inputs

- Allowed category IDs:

```json
{json.dumps(category_ids)}
```

- Category definitions:

```text
{category_list}
```

- Classifier examples:

```json
{examples}
```

- User request:

```text
{request}
```

- story_mode_hint:

```text
{story_mode_hint}
```

---

# Output

Use the required tool. Return only the classification.

---

# Rules

- Choose exactly one `category_id` from the allowed list.
- Use the user request as the main source of classification signals.
- Use `story_mode_hint` only when it clearly matches an allowed category.
- Use classifier examples only for category matching patterns.
- Do not invent categories.
- Do not rewrite the request.
- Do not extract story anchors.
- Do not plan the story.
- Do not generate story content.
- Keep `rationale` short and classification-focused.
- Put only category-relevant evidence in `matched_signals`.

---

# Category Selection Guidance

- Choose `friendship_and_feelings` when the main request is about social feelings, joining, sharing, apologizing, confidence, inclusion, or a small relationship repair.
- Choose `calm_educational_story` when the request asks how or why something works, asks for facts, or wants gentle learning about a real-world concept.
- Choose `cozy_animal_story` when the request centers on an animal, animal home, animal routine, animal-scale practical problem, or animal comfort.
- Choose `gentle_adventure` when the request includes a low-stakes outing, route, errand, delivery, visit, search, exploration, discovery, or return.
- Choose `magical_bedtime_story` when the request includes small magic, enchanted objects, magical clues, fairies, spells, impossible events, or gentle wonder.
- Choose `silly_soft_story` when the request centers on harmless humor, mix-ups, funny objects, playful confusion, or gentle silliness.
- Choose `general_bedtime_story` when the request is ordinary, domestic, routine-based, broadly calm, or does not clearly fit a more specific category.

---

# Tie-Breaking

- If an animal story is mainly about a social feeling or relationship repair, choose `friendship_and_feelings`.
- If an animal story is mainly about animal-scale comfort, home, routine, or a practical problem, choose `cozy_animal_story`.
- If a search has a route, outing, destination, exploration, delivery, or return, choose `gentle_adventure`.
- If a search uses a magical clue, magical helper, enchanted object, or impossible event as the main mechanism, choose `magical_bedtime_story`.
- If a request asks for facts or explanation inside a story, choose `calm_educational_story`.
- If a request is mostly ordinary bedtime routine or domestic care, choose `general_bedtime_story`.

---

# Final Check

Before returning, make sure the category is exactly one allowed category and the response contains no story planning or story prose."""
