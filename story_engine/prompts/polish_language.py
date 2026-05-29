from __future__ import annotations

from typing import Any

_OUTPUT_SCHEMA = """{
  "body": "full polished body"
}"""

LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM = {
    "repetitive_openings": """Problem: repeated mechanical opening
Before: "In the cozy bedroom, Lena looked at Bear on the bed."
After: "Lena looked at Bear on the bed."
Why: removes the mechanical setting label but keeps the same action, character, and place.""",

    "abstract_language": """Problem: abstract feeling summary
Before: "The small fox curled up, feeling safe and content."
After: "The small fox curled up with their nose tucked under their tail."
Why: replaces a feeling label with visible body action without adding a new event.""",

    "generic_mood_words": """Problem: repeated tone words
Before: "The soft glow filled the cozy den with gentle warmth."
After: "The fireflies made small dots of light on the den wall."
Why: keeps the visual comfort but changes mood adjectives into concrete objects.""",

    "quote_formatting": """Problem: quote formatting
Before: "'There it is! ' said Benny."
After: "\\"There it is!\\" Benny said."
Why: fixes quotation marks and punctuation only.""",

    "stiff_or_reported_dialogue": """Problem: dialogue rendered as narration
Before: "The fox whispered that the trail smelled like home."
After: "\\"That smells like home,\\" the fox whispered."
Why: changes reported speech into quoted dialogue without adding a new spoken idea.""",

    "moralizing_ending": """Problem: moral ending
Before: "Benny made room beside Rosie and learned that helping friends is important."
After: "Benny made room beside Rosie."
Why: removes the lesson while keeping the concrete action already present.""",
}

_DEFAULT_EXAMPLE_KEYS = ("abstract_language", "generic_mood_words", "quote_formatting")


def _select_examples_for_failure(failure: Any) -> str:
    reason = (getattr(failure, "reason", "") or "").lower()
    guidance = (getattr(failure, "revision_guidance", "") or "").lower()
    search = reason + " " + guidance
    selected = [k for k in LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM if k in search]
    if not selected:
        selected = list(_DEFAULT_EXAMPLE_KEYS)
    return "\n\n".join(LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM[k] for k in selected)


def build_prompt(draft: Any, failure: Any, blueprint: Any) -> str:
    output_schema = _OUTPUT_SCHEMA
    examples = _select_examples_for_failure(failure)
    return f"""## Role

You are the StoryNest Language Polish Agent.

# Task

Fix only local prose-level problems in the completed story.

Return the full revised story body for packaging.

Do not rewrite the story. Do not repair plot, structure, coherence, safety, request fidelity, or scene planning.

Make the smallest sentence-level edits needed to improve child-readable language, dialogue formatting, repetition, and prose polish while preserving the story’s plot, paragraph structure, and meaning.

---

# Failure

- reason:
````text
{getattr(failure, 'reason', None)}
````

- guidance:
````text
{getattr(failure, 'revision_guidance', None)}
````

---

# Story Body

````text
{draft.body}
````

---

# Output

Return only valid JSON:

````json
{output_schema}
````

---

# Preservation Rules

- Return the full story body.
- Preserve the exact same blank-line-separated paragraph count, paragraph breaks, and paragraph order.
- Make only local sentence-level edits inside existing paragraphs.
- Preserve the same plot, characters, settings, ownership, scene order, actions, dialogue count, resolution, and ending events.
- Do not add, remove, merge, split, summarize, or reorder paragraphs.
- Do not add or remove scenes, characters, objects, problems, clues, discoveries, explanations, dialogue, or resolutions.
- If paragraph preservation is difficult, return the original story body unchanged.

---

# Edit Rules

- Use the failure guidance first.
- Prefer editing the quoted offender text from the failure reason or guidance.
- Fix only the named or clearly implied language problem.
- Replace weak wording with concrete body action, object detail, or story image already present or directly implied nearby.
- Keep the bedtime tone plain, calm, and child-readable.
- Do not make the story more dramatic, exciting, funny, magical, lesson-like, or emotionally explicit.
- Do not add a lesson, moral, new feeling summary, or closing explanation.

---

# Language Targets

Fix these only when named or clearly implied by the failure guidance:

- `abstract_language`: replace abstract feeling, comfort, success, or resolution summaries with visible action or concrete detail already present nearby.
- `generic_mood_words`: reduce repeated words like cozy, soft, gentle, warm, peaceful, magical, glow, or beautiful.
- `scene_card_leakage`: replace planning-like wording with natural story narration.
- `stiff_or_reported_dialogue`: make dialogue brief, natural, quoted, and tied to the action.
- `repetitive_openings`: lightly vary repeated mechanical openings.
- `moralizing_ending`: remove lesson, theme, or feeling-summary language while preserving the final action or image.
- `quote_formatting`: fix quotation marks, spacing, punctuation, and attribution.
- `formulaic_repetition`: reduce repeated sentence patterns, descriptors, or phrases with small local wording changes.

---

# Generic Phrase Cleanup

Replace vague generated-sounding phrases with something visible nearby.

Good local edits:

````text
Before: The room filled with a warm glow as Ella felt a sense of accomplishment.
After: The lamp shone on the notes lined up along Ella's desk.

Before: The paper waited to be discovered.
After: One paper corner stuck out from under the rug.

Before: Leo felt peaceful and content.
After: Leo pulled the blanket to his chin and rested his hand beside the repaired toy.
````

Do not preserve or introduce phrases like `felt a sense of`, `sense of accomplishment`, `heart filled with`, `good deed`, `everything was perfect`, `beautiful day`, `peaceful atmosphere`, `warm glow`, `soft glow`, `gentle breeze`, `waiting to be discovered`, `curiosity piqued`, `suddenly`, `breathtaking`, or `heartwarming`.

Do not replace one vague phrase with another. Replace the phrase with something visible.

---

# Dialogue Rules

- Dialogue must use double quotation marks.
- Keep dialogue brief, natural, and tied to the action.
- Fix quotation marks, spacing, punctuation, and attribution when needed.
- Do not add new dialogue, remove dialogue, or change the speaker's identity.
- Change reported speech into quoted speech only when the sentence already clearly contains reported speech.

---

# Local Edit Examples

Use examples for edit logic only. Do not copy names, objects, dialogue, or sentence patterns.

{examples}

---

# Final Check

Before returning, make sure:

- valid JSON only
- full story body is included
- exact paragraph count, breaks, and order are unchanged
- edits are local and language-focused
- quoted offender text was fixed when possible
- no story event, character, object, dialogue, paragraph, resolution, or ending event was added or removed
- prose avoids repeated phrasing, abstract feelings, moral summaries, and generic filler"""
