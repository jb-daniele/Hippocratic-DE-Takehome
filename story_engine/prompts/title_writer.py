from __future__ import annotations

import json
from typing import Any

_OUTPUT_SCHEMA = """{
  "title": "story title"
}"""


def _plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def build_prompt(blueprint: Any) -> str:
    return f"""# Role

You are the StoryNest Title Writer.

# Task

Create one short, specific, child-friendly title for the completed story.

The title should belong to this exact story, not the category.

---

# Inputs

- category_id: {blueprint.category_id}

- main_characters:
```json
{json.dumps(blueprint.main_characters, ensure_ascii=False)}
```

- story_spine:
```json
{json.dumps(_plain(blueprint.story_spine), ensure_ascii=False, indent=2)}
```

---

# Output

Use the required tool. Return only the title.

---

# Rules

- Create exactly one title.
- Keep the title short: 2-7 words.
- Use Title Case.
- Base the title on a concrete story detail from `story_spine`: character, object, place, action, problem, resolution, or ending image.
- Prefer a specific object, place, action, or repeated detail over a general feeling.
- A character name may appear only if paired with a concrete story detail.
- Do not add concepts or imagery that are not in `story_spine`.
- Do not use category labels or generic title words like Story, Adventure, Journey, Magic, Cozy, Gentle, or Bedtime.
- Do not use a moral, lesson, emotion, or theme as the title.
- Do not use quotation marks, subtitles, colons, dashes, or ending punctuation.

---

# Title Shape

Good title shapes:

```text
[Name] Finds The [Object]
[Name] Returns The [Object]
[Name]'s [Specific Object]
[Name] And The [Specific Object]
The [Specific Object Or Place]
The [Concrete Action Or Problem]
```

Bad titles:

```text
A Cozy Adventure
The Magic Of Friendship
A Story About Helping
The Power Of Kindness
Goodnight, Little Friend
A Lesson In Patience
A Warm And Happy Day
```

---

# Final Check

Before returning, make sure the title is concrete, specific to `story_spine`, 2-7 words, and Title Case."""
