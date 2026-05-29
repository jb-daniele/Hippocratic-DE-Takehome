from __future__ import annotations

import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint
from story_engine.agents.polisher import polish
from story_engine.agents.writer import _paragraph_count
from story_engine.schemas import DraftStory, JudgeReport


def _body(paragraphs: list[str]) -> str:
    return "\n\n".join(paragraphs)


def _eight_paragraph_draft() -> DraftStory:
    paragraphs = [
        "Sunny paragraph 1 holds a gray pebble beside the clover.",
        "Sunny paragraph 2 says felt a sense of peace and accomplishment near Lily.",
        "Sunny paragraph 3 watches the ring-tag circle around the stone.",
        "Sunny paragraph 4 steps from the dandelion shade toward Lily.",
        "Sunny paragraph 5 taps Lily's paw when the circle slows.",
        "Sunny paragraph 6 runs once around the clover marker.",
        "Sunny paragraph 7 laughs beside the gray pebble after the turn.",
        "Sunny paragraph 8 rests with Lily while the clover stems settle.",
    ]
    body = _body(paragraphs)
    scenes = [_body(paragraphs[index:index + 2]) for index in range(0, 8, 2)]
    return DraftStory(title="Sunny Story", body=body, actual_word_count=len(body.split()), scenes=scenes)


def _language_failure() -> JudgeReport:
    return JudgeReport(
        judge_name="language",
        verdict="fail",
        reason='Language is too abstract: "felt a sense of peace and accomplishment".',
        revision_guidance='Replace "felt a sense of peace and accomplishment" with visible action.',
        fail_codes=[],
    )


def _polished_eight_paragraph_body() -> str:
    paragraphs = [
        "Sunny paragraph 1 holds a gray pebble beside the clover.",
        "Sunny paragraph 2 rubs the pebble with his thumb near Lily.",
        "Sunny paragraph 3 watches the ring-tag circle around the stone.",
        "Sunny paragraph 4 steps from the dandelion shade toward Lily.",
        "Sunny paragraph 5 taps Lily's paw when the circle slows.",
        "Sunny paragraph 6 runs once around the clover marker.",
        "Sunny paragraph 7 laughs beside the gray pebble after the turn.",
        "Sunny paragraph 8 rests with Lily while the clover stems settle.",
    ]
    return _body(paragraphs)


def _five_paragraph_body() -> str:
    return _body([f"Collapsed paragraph {index} changes the flagged phrase." for index in range(1, 6)])


def _ten_paragraph_body() -> str:
    return _body([f"Split paragraph {index} changes the flagged phrase." for index in range(1, 11)])


class PolisherParagraphPreservationTests(unittest.TestCase):
    def test_accepts_eight_paragraph_polish(self):
        draft = _eight_paragraph_draft()
        polished_body = _polished_eight_paragraph_body()

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": polished_body}]), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            result = polish(draft, _language_failure(), canonical_blueprint())

        self.assertEqual(_paragraph_count(result.body), 8)
        self.assertEqual(result.body, polished_body)
        self.assertNotEqual(result.body, draft.body)

    def test_rejects_collapsed_output_falls_back_to_original(self):
        draft = _eight_paragraph_draft()

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": _five_paragraph_body()}] * 3), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            result = polish(draft, _language_failure(), canonical_blueprint())

        self.assertEqual(result.body, draft.body)
        self.assertEqual(_paragraph_count(result.body), 8)

    def test_rejects_split_output_falls_back_to_original(self):
        draft = _eight_paragraph_draft()

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": _ten_paragraph_body()}] * 3), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            result = polish(draft, _language_failure(), canonical_blueprint())

        self.assertEqual(result.body, draft.body)
        self.assertEqual(_paragraph_count(result.body), 8)

    def test_retry_prompt_contains_exact_counts(self):
        draft = _eight_paragraph_draft()
        prompts: list[str] = []
        responses = [{"body": _five_paragraph_body()}, {"body": _polished_eight_paragraph_body()}]

        def call_model_json(prompt, **kwargs):
            prompts.append(prompt)
            return responses.pop(0)

        with patch("story_engine.model_client.call_model_json", side_effect=call_model_json), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            polish(draft, _language_failure(), canonical_blueprint())

        self.assertNotIn("from 8 to 5", prompts[0])
        self.assertNotIn("exactly 8 paragraphs", prompts[0])
        self.assertIn("from 8 to 5", prompts[1])
        self.assertIn("exactly 8 paragraphs", prompts[1])

    def test_fallback_logs_paragraph_preservation_degraded_trace(self):
        draft = _eight_paragraph_draft()
        events: list[tuple[str, dict]] = []

        def record_event(event_name, **kwargs):
            events.append((event_name, kwargs))

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": _five_paragraph_body()}] * 3), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ), patch("story_engine.agents.polisher.trace_event", side_effect=record_event), patch(
            "story_engine.agents._common.trace_event", side_effect=record_event
        ):
            polish(draft, _language_failure(), canonical_blueprint())

        self.assertTrue(
            any(
                event_name == "degraded_passthrough"
                and kwargs.get("reason") == "polish_paragraph_preservation_failed input_count=8"
                for event_name, kwargs in events
            )
        )

    def test_retry_recovers_when_second_attempt_returns_eight_paragraphs(self):
        draft = _eight_paragraph_draft()
        recovered_body = _polished_eight_paragraph_body()

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": _five_paragraph_body()}, {"body": recovered_body}]), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            result = polish(draft, _language_failure(), canonical_blueprint())

        self.assertEqual(_paragraph_count(result.body), 8)
        self.assertEqual(result.body, recovered_body)

    def test_fallback_preserves_original_eight_paragraphs(self):
        draft = _eight_paragraph_draft()

        with patch("story_engine.model_client.call_model_json", side_effect=[{"body": _five_paragraph_body()}] * 3), patch(
            "story_engine.model_client.log_validator_decision", lambda **kwargs: None
        ):
            result = polish(draft, _language_failure(), canonical_blueprint())

        self.assertEqual(result.body, draft.body)
        self.assertEqual(_paragraph_count(result.body), 8)


if __name__ == "__main__":
    unittest.main()
