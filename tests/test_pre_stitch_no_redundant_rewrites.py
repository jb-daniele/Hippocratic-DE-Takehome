import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import pipeline
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


def _draft_from_blueprint(blueprint):
    scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
    body = "\n\n".join(scenes)
    return DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)


class PreStitchResidualTests(unittest.TestCase):
    def test_pre_stitch_ignores_hits_already_recorded_by_writer(self):
        blueprint = canonical_blueprint()
        draft = _draft_from_blueprint(blueprint)
        object.__setattr__(draft, "_writer_residuals", [["missing_setting"], [], [], []])
        stubbed_hits = [
            [{"code": "missing_setting", "evidence": "same residual"}],
            [],
            [],
            [],
        ]
        with patch("story_engine.pipeline.write.validate_written_scene", side_effect=stubbed_hits):
            failures = pipeline._pre_stitch_scene_failures(draft, blueprint)
        self.assertEqual(failures, [])

    def test_pre_stitch_surfaces_new_hits_not_seen_by_writer(self):
        blueprint = canonical_blueprint()
        draft = _draft_from_blueprint(blueprint)
        object.__setattr__(draft, "_writer_residuals", [["missing_setting"], [], [], []])
        stubbed_hits = [
            [{"code": "missing_dialogue", "evidence": "new residual"}],
            [],
            [],
            [],
        ]
        with patch("story_engine.pipeline.write.validate_written_scene", side_effect=stubbed_hits):
            failures = pipeline._pre_stitch_scene_failures(draft, blueprint)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["scene_index"], 1)
        self.assertEqual(failures[0]["hard_failures"], ["missing_dialogue"])
