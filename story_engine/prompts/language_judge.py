from __future__ import annotations

from typing import Any


LANGUAGE_JUDGE_FAILURE_CODES = [
    "tense_drift",
    "abstract_language",
    "generic_mood_words",
    "scene_card_leakage",
    "stiff_or_reported_dialogue",
    "repetitive_openings",
    "moralizing_ending",
    "quote_formatting",
    "formulaic_repetition",
]

LANGUAGE_JUDGE_FAILURE_CODE_DESCRIPTIONS = [
    "`tense_drift`: narration uses present tense or switches between present and past tense instead of staying in simple past tense.",
    "`abstract_language`: feelings, success, comfort, or resolution are summarized instead of shown through visible body action, object detail, or story image.",
    "`generic_mood_words`: repeated cozy/soft/gentle/warm/peaceful/magical/glow-style words make the prose generic.",
    "`scene_card_leakage`: prose sounds like planning notes or SceneCard functions instead of natural story narration.",
    "`stiff_or_reported_dialogue`: dialogue is awkward, unnatural, or narrated as reported speech instead of quoted speech.",
    "`repetitive_openings`: multiple paragraphs or scenes begin with the same mechanical setup pattern.",
    "`moralizing_ending`: the final paragraph ends with a lesson, theme statement, or abstract feeling summary instead of story prose.",
    "`quote_formatting`: quote marks, punctuation, or spacing around dialogue are visibly malformed.",
    "`formulaic_repetition`: repeated sentence patterns or phrases make the story sound mechanically generated.",
]

def build_prompt(draft: Any) -> str:
    failure_codes = LANGUAGE_JUDGE_FAILURE_CODE_DESCRIPTIONS
    return f"""# Role

You are the StoryNest Language Judge.

# Task

Judge only local prose-quality problems that Language Polish can fix.

Do not rewrite the story.  
Do not judge plot, coherence, safety, request fidelity, resolution quality, ending-image correctness, or SceneCard compliance.

Fail only for clear prose problems that are repeated, prominent, or appear in an important place such as dialogue, scene openings, or the ending.

---

# Input

- story_body:
````text
{draft.body}
````

---

# Output

Use the required tool. Return only the language judgment.
Example: {{"verdict": "fail", "failures": [{{"code": "abstract_language", "evidence": "felt a sense of peace", "revision_guidance": "Replace the abstract feeling summary with visible body action."}}]}}

Allowed failure codes:

````text
{failure_codes}
````

---

# Pass / Fail Standard

Pass if the story is readable, child-clear, mostly concrete, and only mildly plain.

Fail if local polish should fix any prominent or repeated issue below:

- `tense_drift`: narration uses present tense or switches between present and past tense
- `abstract_language`: abstract feeling, comfort, success, or resolution summaries replace visible story prose
- `generic_mood_words`: repeated cozy, soft, gentle, warm, peaceful, magical, glow, or beautiful-style mood words make the prose generic
- `formulaic_repetition`: repeated sentence openings, sentence rhythms, descriptors, or action phrases make the story sound mechanical
- `stiff_or_reported_dialogue`: dialogue is reported, stiff, malformed, or not natural quoted speech
- `scene_card_leakage`: planning-like wording appears in the story
- `repetitive_openings`: scenes repeatedly open with mechanical phrasing such as “In/At [setting]...”
- `moralizing_ending`: the ending turns into a lesson, theme statement, or feeling summary
- `quote_formatting`: quotation errors interfere with read-aloud flow

Do not fail for ordinary simple wording, calm bedtime tone, short sentences, one plain transition, or one or two mild mood words.

---

# Generic Phrase Triggers

Fail when phrases like these are repeated, prominent, or appear in the ending or dialogue:

````text
felt a sense of, sense of accomplishment, heart filled with, filled their hearts, good deed, everything was perfect, beautiful day, peaceful atmosphere, warm glow, soft glow, gentle breeze, waiting to be discovered, curiosity piqued, suddenly, breathtaking, heartwarming
````

Do not pass these just because the story is coherent, safe, or understandable.

---

# Evidence Rules

For each failure:

- quote the exact local phrase or sentence Polish should fix
- keep evidence under 120 characters
- use the clearest quote for repeated problems
- for ending problems, quote the ending phrase
- for tense drift, quote one present-tense narration phrase

---

# Revision Guidance

Write one brief local-polish instruction per failure.

Good guidance:

````text
Change present-tense narration into simple past tense.
Replace abstract feeling summary with visible action or object detail.
Reduce repeated mood wording and use concrete objects already in the scene.
Change reported speech into quoted dialogue only where speech is already implied.
Remove the moral/theme summary and keep the final story image.
````

Do not ask Polish to rewrite scenes, change plot, add events, add characters, add objects, fix structure, fix safety, or make the story more exciting.

---

# Final Check

Before returning, make sure:

- If you include any failure, `verdict` must be `"fail"`. If `verdict` is `"pass"`, `failures` must be empty.
- you judged prose only
- each failure is locally polishable
- each failure has a short quote
- repeated tense drift, formulaic phrasing, generic mood language, or abstract ending language was not ignored
- minor plain wording did not cause a failure
"""
