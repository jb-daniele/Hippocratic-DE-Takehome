import unittest
from unittest.mock import patch

from _helpers import stub_llm
from story_engine import model_client, pipeline
from story_engine.schemas import RequestOptions


class PipelineHappyPathTests(unittest.TestCase):
    def test_pipeline_run_friendship_mode_returns_approved_package(self):
        stub = stub_llm("friendship_and_feelings")
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ):
            package = pipeline.run(
                "a friendship story about Sunny mole joining ring-tag",
                RequestOptions(story_mode="friendship", main_character_name="Sunny"),
            )
        self.assertEqual(len([paragraph for paragraph in package.story.body.split("\n\n") if paragraph.strip()]), 8)
        self.assertTrue(package.approved)
        self.assertEqual(package.cover["category_id"], "friendship_and_feelings")
        self.assertEqual(package.story.title, "Sunny and the Clover Circle")

    def test_pipeline_run_animal_mode_returns_approved_package(self):
        stub = stub_llm("cozy_animal_story")
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ):
            package = pipeline.run(
                "a cozy animal story about Sunny fixing a leaf roof",
                RequestOptions(story_mode="animal", main_character_name="Sunny"),
            )
        self.assertEqual(len([paragraph for paragraph in package.story.body.split("\n\n") if paragraph.strip()]), 8)
        self.assertTrue(package.approved)
        self.assertEqual(package.cover["category_id"], "cozy_animal_story")
        self.assertEqual(package.story.title, "Sunny and the Leaf Roof")
