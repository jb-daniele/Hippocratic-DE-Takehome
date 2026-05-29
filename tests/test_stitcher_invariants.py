import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import agents, model_client
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


def _draft():
    blueprint = canonical_blueprint()
    scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
    body = "\n\n".join(scenes)
    draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
    return blueprint, draft


def _paragraphs(text: str) -> list[str]:
    return [paragraph for paragraph in text.split("\n\n") if paragraph.strip()]


def _stitch_failure(draft: DraftStory) -> dict:
    return {
        "boundary_indexes": [1],
        "seam_failures": [{"boundary_index": 1, "kind": "duplicate_adjacent_sentence", "evidence": "x"}],
        "expected_paragraph_count": len(_paragraphs(draft.body)),
    }


def _truncate_body_to_ratio(body: str, ratio: float) -> str:
    truncated: list[str] = []
    for paragraph in _paragraphs(body):
        words = paragraph.split()
        keep = max(1, int(len(words) * ratio))
        truncated.append(" ".join(words[:keep]))
    return "\n\n".join(truncated)


def _expand_body_to_ratio(body: str, ratio: float) -> str:
    expanded: list[str] = []
    for paragraph in _paragraphs(body):
        words = paragraph.split()
        extra = max(1, int(len(words) * (ratio - 1.0)))
        expanded.append(f"{paragraph} {' '.join(['bridge'] * extra)}")
    return "\n\n".join(expanded)


def _assembled_body_from_prompt(prompt: str) -> str:
    marker = "# Assembled Body\n\n```text\n"
    start = prompt.index(marker) + len(marker)
    end = prompt.index("\n```", start)
    return prompt[start:end]


class StitcherInvariantTests(unittest.TestCase):
    def test_stitcher_output_within_word_count_band_passes(self):
        blueprint, draft = _draft()
        with patch.object(model_client, "call_model_json", return_value={"body": draft.body}):
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched.actual_word_count, draft.actual_word_count)

    def test_seven_paragraph_stitcher_output_degrades_to_original_eight_paragraphs(self):
        blueprint, draft = _draft()
        seven_paragraph_body = "\n\n".join(draft.body.split("\n\n")[:-1])
        with patch.object(model_client, "call_model_json", return_value={"body": seven_paragraph_body}):
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(len([paragraph for paragraph in stitched.body.split("\n\n") if paragraph.strip()]), 8)
        self.assertEqual(stitched.body, draft.body)

    def test_quote_count_change_degrades_to_original_body(self):
        blueprint, draft = _draft()
        with patch.object(model_client, "call_model_json", return_value={"body": draft.body + '"'}):
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched.body.count('"'), draft.body.count('"'))

    def test_truncated_output_below_ninety_percent_returns_original_body_after_one_attempt(self):
        blueprint, draft = _draft()
        short_body = _truncate_body_to_ratio(draft.body, 0.6)
        with patch.object(model_client, "call_model_json", return_value={"body": short_body}) as stitched_call:
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched_call.call_count, 1)

    def test_expanded_output_above_one_hundred_ten_percent_returns_original_body_after_one_attempt(self):
        blueprint, draft = _draft()
        long_body = _expand_body_to_ratio(draft.body, 1.25)
        with patch.object(model_client, "call_model_json", return_value={"body": long_body}) as stitched_call:
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched_call.call_count, 1)

    def test_failed_attempt_returns_original_assembled_body(self):
        blueprint, draft = _draft()
        short_body = _truncate_body_to_ratio(draft.body, 0.6)
        with patch.object(model_client, "call_model_json", return_value={"body": short_body}) as stitched_call:
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched_call.call_count, 1)

    def test_single_attempt_uses_original_assembled_body_in_prompt(self):
        blueprint, draft = _draft()
        prompts: list[str] = []

        def side_effect(prompt, **kwargs):
            prompts.append(prompt)
            return {"body": _truncate_body_to_ratio(draft.body, 0.6)}

        with patch.object(model_client, "call_model_json", side_effect=side_effect) as stitched_call:
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched_call.call_count, 1)
        self.assertEqual(_assembled_body_from_prompt(prompts[0]), draft.body)
