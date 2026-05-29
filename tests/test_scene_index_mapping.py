import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, stub_llm, varied_scene_paragraphs
from story_engine import model_client, pipeline
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory, RequestOptions


def _draft_from_blueprint(blueprint):
    scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
    body = "\n\n".join(scenes)
    return DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)


class SceneIndexMappingTests(unittest.TestCase):
    def test_continuity_break_scene_index_two_targets_second_scene(self):
        blueprint = canonical_blueprint()
        draft = _draft_from_blueprint(blueprint)
        called_scenes = []

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            called_scenes.append(card.scene)
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        with patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            pipeline._repair_scene_failures(
                draft,
                blueprint,
                [{"code": "continuity_break", "scene_index": 2, "issues": ["x"], "source": "coherence_judge"}],
            )
        self.assertEqual(called_scenes, [2])

    def test_missing_resolution_without_scene_index_targets_third_scene(self):
        blueprint = canonical_blueprint()
        draft = _draft_from_blueprint(blueprint)
        called_scenes = []

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            called_scenes.append(card.scene)
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        with patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            pipeline._repair_scene_failures(
                draft,
                blueprint,
                [{"code": "missing_resolution", "scene_index": None, "issues": ["x"], "source": "coherence_judge"}],
            )
        self.assertEqual(called_scenes, [3])

    def test_missing_ending_image_without_scene_index_targets_fourth_scene(self):
        blueprint = canonical_blueprint()
        draft = _draft_from_blueprint(blueprint)
        called_scenes = []

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            called_scenes.append(card.scene)
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        with patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            pipeline._repair_scene_failures(
                draft,
                blueprint,
                [{"code": "missing_ending_image", "scene_index": None, "issues": ["x"], "source": "coherence_judge"}],
            )
        self.assertEqual(called_scenes, [4])

    def test_request_drift_without_scene_index_targets_fourth_scene_and_warns(self):
        calls = []
        responses = iter(
            [
                {"passed": False, "fail_codes": [{"code": "request_drift", "evidence": "x", "scene_index": None}]},
                {"passed": True, "fail_codes": []},
            ]
        )

        def coherence_judge_override(prompt, **kwargs):
            return next(responses)

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            calls.append(card.scene)
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        stub = stub_llm("friendship_and_feelings", coherence_judge=coherence_judge_override)
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        self.assertEqual(calls, [4])
        self.assertTrue(any("request_drift routed to scene 4 by default" in warning for warning in package.warnings))

    def test_ownership_drift_without_scene_index_targets_fourth_scene_and_warns(self):
        calls = []
        responses = iter(
            [
                {"passed": False, "fail_codes": [{"code": "ownership_drift", "evidence": "x", "scene_index": None}]},
                {"passed": True, "fail_codes": []},
            ]
        )

        def coherence_judge_override(prompt, **kwargs):
            return next(responses)

        def fake_rewrite(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            calls.append(card.scene)
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": []}

        stub = stub_llm("friendship_and_feelings", coherence_judge=coherence_judge_override)
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.write.rewrite_scene", side_effect=fake_rewrite):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        self.assertEqual(calls, [4])
        self.assertTrue(any("ownership_drift routed to scene 4 by default" in warning for warning in package.warnings))
