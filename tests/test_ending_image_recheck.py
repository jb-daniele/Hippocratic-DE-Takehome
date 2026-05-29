import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import pipeline
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


def _draft_missing_ending_image(blueprint):
    scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
    scenes[-1] = (
        "Quiet grass dimmed around Sunny while the last game marker leaned by the path.\n\n"
        "The evening stayed quiet and plain."
    )
    body = "\n\n".join(scenes)
    return DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)


class EndingImageRecheckTests(unittest.TestCase):
    def test_repair_scene_failures_warns_when_ending_image_still_missing(self):
        blueprint = canonical_blueprint()
        draft = _draft_missing_ending_image(blueprint)

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        with patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            _repaired, warnings = pipeline._repair_scene_failures(
                draft,
                blueprint,
                [{"code": "missing_ending_image", "scene_index": 4, "issues": ["x"], "source": "coherence_judge"}],
            )
        self.assertIn("ending_image still failing after scene 4 rewrite", warnings)

    def test_repair_scene_failures_skips_warning_when_ending_image_is_restored(self):
        blueprint = canonical_blueprint()
        draft = _draft_missing_ending_image(blueprint)
        repaired_scene = "\n\n".join(varied_scene_paragraphs(3, blueprint.scene_cards[3])["paragraphs"])

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            return {"body": repaired_scene, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        with patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            _repaired, warnings = pipeline._repair_scene_failures(
                draft,
                blueprint,
                [{"code": "missing_ending_image", "scene_index": 4, "issues": ["x"], "source": "coherence_judge"}],
            )
        self.assertNotIn("ending_image still failing after scene 4 rewrite", warnings)
