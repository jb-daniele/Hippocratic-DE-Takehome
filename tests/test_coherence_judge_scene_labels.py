"""Follow-up: verify evidence quote appears in scene matching scene_index; deferred."""

import re
import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, canonical_classification
from story_engine.agents import judges
from story_engine.prompts.coherence_judge import build_prompt
from story_engine.schemas import DraftStory
from story_engine.text.scene_split import split_scenes


def _draft(body, scenes=None):
    return DraftStory(title="Sunny Story", body=body, actual_word_count=len(body.split()), scenes=scenes or [])


def _paragraph_body(count, prefix="Paragraph"):
    return "\n\n".join(f"{prefix} {index} text." for index in range(1, count + 1))


def _story_body_block(prompt):
    match = re.search(r"# Story Body\n\n```text\n(.*?)\n```\n\n---", prompt, re.DOTALL)
    if match is None:
        raise AssertionError("Story Body block not found")
    return match.group(1)


class CoherenceJudgeSceneLabelTests(unittest.TestCase):
    def test_labeled_scenes_from_paragraphs(self):
        blueprint = canonical_blueprint()
        classification = canonical_classification()
        draft = _draft(_paragraph_body(8), scenes=[])
        scenes = split_scenes(draft.body, blueprint, draft=draft)

        prompt = build_prompt(draft, blueprint, classification, classification.request_text, scenes=scenes)
        story_block = _story_body_block(prompt)

        for index in range(1, 5):
            self.assertIn(f"Scene {index}:", story_block)
        self.assertRegex(story_block, r"Scene 1:\nParagraph 1 text\.\n\nParagraph 2 text\.")
        self.assertRegex(story_block, r"Scene 2:\nParagraph 3 text\.\n\nParagraph 4 text\.")
        self.assertRegex(story_block, r"Scene 3:\nParagraph 5 text\.\n\nParagraph 6 text\.")
        self.assertRegex(story_block, r"Scene 4:\nParagraph 7 text\.\n\nParagraph 8 text\.")

    def test_labeled_scenes_prefers_draft_scenes(self):
        blueprint = canonical_blueprint()
        classification = canonical_classification()
        sentinels = [f"SENTINEL SCENE {index}" for index in range(1, 5)]
        draft = _draft(_paragraph_body(8, prefix="pat"), scenes=sentinels)
        scenes = split_scenes(draft.body, blueprint, draft=draft)

        prompt = build_prompt(draft, blueprint, classification, classification.request_text, scenes=scenes)
        story_block = _story_body_block(prompt)

        for index, sentinel in enumerate(sentinels, start=1):
            self.assertIn(f"Scene {index}:\n{sentinel}", story_block)
        self.assertNotIn("pat 1 text.", story_block)

    def test_split_scenes_with_empty_element_triggers_judge_fallback(self):
        blueprint = canonical_blueprint()
        classification = canonical_classification()
        draft = _draft(_paragraph_body(3), scenes=[])
        events = []
        prompt_kwargs = {}

        self.assertEqual(split_scenes(draft.body, blueprint, draft=draft), ["Paragraph 1 text.", "Paragraph 2 text.", "Paragraph 3 text.", ""])

        def fake_build(*args, **kwargs):
            prompt_kwargs.update(kwargs)
            return "prompt"

        with patch.object(judges, "build_coherence_judge_prompt", side_effect=fake_build), patch.object(
            judges.model_client, "call_model_tool", return_value={"passed": True, "fail_codes": []}
        ), patch.object(
            judges, "trace_event", side_effect=lambda event_name, **kwargs: events.append((event_name, kwargs))
        ):
            judges.judge_coherence(draft, blueprint, classification, classification.request_text)

        degraded = [event for event in events if event[0] == "agents.coherence_judge.scene_labels_degraded"]
        self.assertIsNone(prompt_kwargs["scenes"])
        self.assertEqual(len(degraded), 1)
        self.assertEqual(degraded[0][1]["reason"], "empty_element")

    def test_judge_coherence_emits_degradation_trace(self):
        blueprint = canonical_blueprint()
        classification = canonical_classification()
        draft = _draft(_paragraph_body(8), scenes=[])
        events = []
        prompt_kwargs = {}

        def fake_build(*args, **kwargs):
            prompt_kwargs.update(kwargs)
            return "prompt"

        with patch.object(judges, "split_scenes", return_value=[]), patch.object(
            judges, "build_coherence_judge_prompt", side_effect=fake_build
        ), patch.object(judges.model_client, "call_model_tool", return_value={"passed": True, "fail_codes": []}), patch.object(
            judges, "trace_event", side_effect=lambda event_name, **kwargs: events.append((event_name, kwargs))
        ):
            judges.judge_coherence(draft, blueprint, classification, classification.request_text)

        degraded = [event for event in events if event[0] == "agents.coherence_judge.scene_labels_degraded"]
        self.assertEqual(len(degraded), 1)
        self.assertIn("reason", degraded[0][1])
        self.assertIsNone(prompt_kwargs["scenes"])

    def test_judge_coherence_passes_labeled_scenes(self):
        blueprint = canonical_blueprint()
        classification = canonical_classification()
        draft = _draft(_paragraph_body(8), scenes=[])
        captured_kwargs = {}
        real_builder = build_prompt

        def capturing_build(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return real_builder(*args, **kwargs)

        with patch.object(judges, "build_coherence_judge_prompt", side_effect=capturing_build), patch.object(
            judges.model_client, "call_model_tool", return_value={"passed": True, "fail_codes": []}
        ):
            judges.judge_coherence(draft, blueprint, classification, classification.request_text)

        scenes = captured_kwargs["scenes"]
        self.assertEqual(len(scenes), 4)
        self.assertTrue(all(scene.strip() for scene in scenes))
        prompt = real_builder(draft, blueprint, classification, classification.request_text, scenes=scenes)
        self.assertIn("Scene 1:", prompt)


if __name__ == "__main__":
    unittest.main()
