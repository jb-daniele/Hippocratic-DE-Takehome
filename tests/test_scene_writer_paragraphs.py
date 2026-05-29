import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import agents, model_client


class SceneWriterTests(unittest.TestCase):
    def test_write_scene_result_returns_two_paragraph_body(self):
        blueprint = canonical_blueprint()
        card = blueprint.scene_cards[0]
        with patch.object(model_client, "call_model_json", side_effect=lambda prompt, **kwargs: varied_scene_paragraphs(kwargs["scene_index"], card)):
            body, fallback, residuals = agents._write_scene_result(blueprint, scene_index=0)
        paragraphs = [paragraph for paragraph in body.split("\n\n") if paragraph.strip()]
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(agents.validate_written_scene(body, card), [])
        self.assertFalse(fallback)
        self.assertEqual(residuals, [])

    def test_write_scene_result_returns_fallback_flag_for_residual_failures(self):
        blueprint = canonical_blueprint()
        card = blueprint.scene_cards[0]
        payload = varied_scene_paragraphs(0, card)
        payload["paragraphs"][0] = payload["paragraphs"][0].replace("Meadow", "Fieldless", 1)
        with patch.object(
            model_client, "call_model_json",
            return_value=payload,
        ):
            body, fallback, residuals = agents._write_scene_result(blueprint, scene_index=0)
        self.assertTrue(fallback)
        self.assertEqual(len([paragraph for paragraph in body.split("\n\n") if paragraph.strip()]), 2)
        self.assertEqual(residuals[0]["code"], "missing_setting")

    def test_retry_prompt_includes_code_specific_guidance_for_known_failure(self):
        blueprint = canonical_blueprint()
        card = blueprint.scene_cards[0]
        failing_payload = varied_scene_paragraphs(0, card)
        failing_payload["paragraphs"][0] = failing_payload["paragraphs"][0].replace("Meadow", "Fieldless", 1)
        passing_payload = varied_scene_paragraphs(0, card)

        with patch.object(model_client, "call_model_json", side_effect=[failing_payload, passing_payload]) as mocked_call:
            body, fallback, residuals = agents._write_scene_result(blueprint, scene_index=0)

        retry_prompt = mocked_call.call_args_list[1].args[0]
        self.assertIn(
            "Your previous scene still failed `missing_setting`. The next output must visibly show the SceneCard setting through a concrete place or object detail.",
            retry_prompt,
        )
        self.assertIn("## Code-specific repair guidance", retry_prompt)
        self.assertIn("Return the complete scene again.", retry_prompt)
        self.assertFalse(fallback)
        self.assertEqual(residuals, [])
        self.assertEqual(agents.validate_written_scene(body, card), [])

    def test_retry_prompt_omits_code_specific_guidance_for_unknown_failure(self):
        blueprint = canonical_blueprint()
        card = blueprint.scene_cards[0]
        malformed_payload = {"paragraphs": ["Only one paragraph."]}
        passing_payload = varied_scene_paragraphs(0, card)

        with patch.object(model_client, "call_model_json", side_effect=[malformed_payload, passing_payload]) as mocked_call:
            body, fallback, residuals = agents._write_scene_result(blueprint, scene_index=0)

        retry_prompt = mocked_call.call_args_list[1].args[0]
        self.assertIn("## Repair", retry_prompt)
        self.assertNotIn("## Code-specific repair guidance", retry_prompt)
        self.assertFalse(fallback)
        self.assertEqual(residuals, [])
        self.assertEqual(agents.validate_written_scene(body, card), [])

    def test_write_draft_attaches_writer_residuals(self):
        blueprint = canonical_blueprint()
        scene_bodies = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]

        def fake_write_scene_result(blueprint, scene_index, already_written_summary="", upcoming_scene_summary=""):
            if scene_index == 0:
                return scene_bodies[scene_index], False, [{"code": "missing_setting", "evidence": "same residual"}]
            return scene_bodies[scene_index], False, []

        def fake_rewrite_scene(card, failed_scene_text, fail_codes_with_evidence, **kwargs):
            return {"body": failed_scene_text, "addresses_codes": [item["code"] for item in fail_codes_with_evidence], "residual_failures": fail_codes_with_evidence}

        with patch("story_engine.agents.writer._write_scene_result", side_effect=fake_write_scene_result), patch(
            "story_engine.agents.writer.rewrite_scene",
            side_effect=fake_rewrite_scene,
        ):
            draft = agents.write_draft(blueprint)
        self.assertEqual(getattr(draft, "_writer_residuals"), [["missing_setting"], [], [], []])
