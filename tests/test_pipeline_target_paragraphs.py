import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, stub_llm, varied_scene_paragraphs
from story_engine import model_client, pipeline
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory, RequestOptions


class PipelineTargetParagraphTests(unittest.TestCase):
    def test_happy_path_returns_target_paragraph_final_body(self):
        stub = stub_llm("friendship_and_feelings")
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        expected = package.blueprint.scene_plan["scene_count"] * package.blueprint.scene_plan["paragraphs_per_scene"]
        self.assertEqual(len([paragraph for paragraph in package.story.body.split("\n\n") if paragraph.strip()]), expected)

    def test_seven_paragraph_stitch_output_falls_back_to_assembled_body(self):
        blueprint = canonical_blueprint()
        scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
        assembled_body = "\n\n".join(scenes)
        seven_paragraph_body = "\n\n".join("\n\n".join(scenes).split("\n\n")[:-1])
        seven_paragraph_draft = DraftStory(
            title=blueprint.title,
            body=seven_paragraph_body,
            actual_word_count=calculate_word_count(seven_paragraph_body),
            scenes=[],
        )
        stub = stub_llm("friendship_and_feelings")
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.SCENE_STITCHER_BYPASS_ENABLED", False), patch(
            "story_engine.pipeline.stitch_scenes", return_value=seven_paragraph_draft
        ):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        self.assertEqual(package.story.body, assembled_body)
        self.assertIn("stitched_output_invalid; using assembled body", package.warnings)

    def test_post_draft_report_checks_omit_paragraph_count(self):
        stub = stub_llm("friendship_and_feelings")
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        self.assertNotIn("paragraph_count", package.cover["post_draft_report"]["checks"])
