from __future__ import annotations

import json
from typing import Any

from story_engine.prompts.paragraph_structures import character_guide_for

#For prompt engineering reference only
_OUTPUT_SCHEMA = """{
  "cast": [
    {
      "name": "character name",
      "pronouns": "she/her | he/him | they/them",
      "kind": "child, animal, caregiver, fairy, toy, etc.",
      "role": "short practical story function"
    }
  ]
}"""


def build_prompt(classification: Any) -> str:
    names = json.dumps([character.name for character in classification.main_characters], ensure_ascii=False)
    guide = character_guide_for(classification.category_id)
    return f"""# Role

You are the StoryNest Character Designer.

# Inputs

- category_id: {classification.category_id}

- category_guide:
```text
{guide}
```

- request:
```text
{classification.request_text}
```

- character_names:
```json
{names}
```

# Task

Create a short cast list for story planning.

Do not write story prose.  
Do not plan the central problem, resolution, or scene beats.

---

# Rules

- Use the request first; use `category_guide` only for category fit.
- Preserve any named character, requested helper, animal, caregiver, object character, or important relationship from the request.
- Create cast entries for listed `character_names`.
- If no `character_names` are listed, create the smallest cast needed for the request.
- If the request describes multiple unnamed individual characters, give each one a simple child-friendly name.
- Do not use placeholder names like “Child 1,” “Child 2,” “Cousin 1,” “Cousin 2,” “Friend 1,” “Sibling 2,” “Animal 1,” or “Main Character” unless the user specifically named them that way.
- Preserve requested relationships in `kind` or `role`, not by using placeholder names.
- Do not add a support character unless the request clearly needs one for a shared activity, caregiving, dialogue, or a simple explanation.
- Do not add a helper that could replace or compete with a requested object, clue, activity, mechanism, or outcome.
- Do not create more than two characters unless the request or `character_names` requires more.
- Do not replace a user-requested helper with a different helper.
- For individual characters, use `she/her` or `he/him` by default.
- Do not use `they/them` for an individual character unless the user specifically requests `they/them`, the character is explicitly nonbinary, or the cast entry represents a group.
- `pronouns` must be exactly one of: `"she/her"`, `"he/him"`, `"they/them"`.
- `kind` must say what the character is, such as `"child"`, `"child cousin"`, `"mole"`, `"rabbit"`, `"mother"`, `"fairy"`, or `"stuffed bear"`.
- `role` must describe the character's broad practical function in the request.
- Do not use `role` to decide the central problem, resolution, helper action, or scene beats.
- Keep roles broad enough for Arc Planner to decide the story path.
- Avoid personality or mood labels like supportive, cheerful, determined, gentle, wise, kind, playful, brave, or creative.
- Keep every field brief and operational.

---

# Output

Use the required tool. Return only the cast.

---

# Name Quality

Good names for unnamed individual characters:

```text
Maya
Leo
Nora
Tessa
Milo
Lena
Suri
```

Bad placeholder names:

```text
Child 1
Cousin 1
Friend 2
Sibling A
Animal 1
Main Character
```

---

# Role Quality

Good roles:

```text
main child in the requested activity
second child in the shared activity
caregiver available for one practical step
animal with the small home problem
friend in the shared game
object character involved in the bedtime routine
adult available for a safe observation
```

Weak roles:

```text
kind friend
wise helper
playful cousin
creative child
supportive companion
helper who makes everything better
character who learns a lesson
```

Too specific for Character Designer:

```text
holds the loose roof leaf in place
brings the missing repair material
combines the two shadow ideas
explains why drops form on the spoon
points to the next route landmark
```

---

# Final Check

Before returning, make sure:

- the cast preserves requested characters, helpers, and relationships
- unnamed individual characters have simple names, not placeholder labels
- no added support character replaces the requested story mechanism
- individual characters use `she/her` or `he/him` unless the request specifically allows `they/them`
- roles are broad practical functions, not character bios or story beats"""
