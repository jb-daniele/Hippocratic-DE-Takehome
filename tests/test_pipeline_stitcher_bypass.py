import json
import unittest
from unittest.mock import Mock, patch

from _helpers import stub_llm
from story_engine import model_client, pipeline
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory, RequestOptions


def _run_pipeline():
    return pipeline.run(
        "a friendship story about Sunny mole joining ring-tag",
        RequestOptions(story_mode="friendship", main_character_name="Sunny"),
    )


def _paragraph_count(text: str) -> int:
    return len([paragraph for paragraph in text.split("\n\n") if paragraph.strip()])


def _assembled_body_from_prompt(prompt: str) -> str:
    marker = "# Assembled Body\n\n```text\n"
    start = prompt.index(marker) + len(marker)
    end = prompt.index("\n```", start)
    return prompt[start:end]


def _stitch_failure_from_prompt(prompt: str) -> dict:
    marker = "- stitch_failure:\n```json\n"
    start = prompt.index(marker) + len(marker)
    end = prompt.index("\n```", start)
    return json.loads(prompt[start:end])


class PipelineStitcherBypassTests(unittest.TestCase):
    def test_clean_seams_skip_stitcher(self):
        stub = stub_llm("friendship_and_feelings")
        forbidden = Mock(side_effect=AssertionError("stitcher should be bypassed"))
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.stitch_scenes", forbidden):
            package = _run_pipeline()
        self.assertTrue(package.approved)
        self.assertEqual(_paragraph_count(package.story.body), 8)
        forbidden.assert_not_called()

    def test_dirty_seams_invoke_stitcher_once(self):
        base_stub = stub_llm("friendship_and_feelings")

        def scene_writer_override(prompt, **kwargs):
            payload = base_stub(prompt, **kwargs)
            if kwargs.get("scene_index") == 0:
                paragraphs = list(payload["paragraphs"])
                paragraphs[-1] = f'{paragraphs[-1]} Shared seam sentence.'
                return {"paragraphs": paragraphs}
            if kwargs.get("scene_index") == 1:
                paragraphs = list(payload["paragraphs"])
                paragraphs[0] = f"Shared seam sentence. {paragraphs[0]}"
                return {"paragraphs": paragraphs}
            return payload

        base_recording_stub = stub_llm("friendship_and_feelings", scene_writer=scene_writer_override)
        prompts: list[str] = []

        def recording_stub(prompt, **kwargs):
            if kwargs.get("agent_name") == "scene_stitcher":
                prompts.append(prompt)
            return base_recording_stub(prompt, **kwargs)

        with patch.object(model_client, "call_model_json", side_effect=recording_stub), patch.object(model_client, "call_model_tool", side_effect=recording_stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.stitch_scenes", wraps=pipeline.stitch_scenes) as stitched:
            package = _run_pipeline()
        self.assertEqual(stitched.call_count, 1)
        self.assertEqual(_paragraph_count(package.story.body), 8)
        self.assertEqual(len(prompts), 1)
        stitch_failure = _stitch_failure_from_prompt(prompts[0])
        assembled_body = _assembled_body_from_prompt(prompts[0])
        self.assertIn("boundary_indexes", prompts[0])
        self.assertIn("duplicate_adjacent_sentence", prompts[0])
        self.assertIn("Shared seam sentence", prompts[0])
        self.assertEqual(stitch_failure["expected_paragraph_count"], _paragraph_count(assembled_body))

    def test_divergent_stitched_output_falls_back_to_assembled_body(self):
        base_stub = stub_llm("friendship_and_feelings")

        def scene_writer_override(prompt, **kwargs):
            payload = base_stub(prompt, **kwargs)
            if kwargs.get("scene_index") == 0:
                paragraphs = list(payload["paragraphs"])
                paragraphs[-1] = f'{paragraphs[-1]} Shared seam sentence.'
                return {"paragraphs": paragraphs}
            if kwargs.get("scene_index") == 1:
                paragraphs = list(payload["paragraphs"])
                paragraphs[0] = f"Shared seam sentence. {paragraphs[0]}"
                return {"paragraphs": paragraphs}
            return payload

        stub = stub_llm("friendship_and_feelings", scene_writer=scene_writer_override)
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ):
            pre_package = _run_pipeline()
        assembled_body = pre_package.story.body
        reversed_body = "\n\n".join(reversed([paragraph for paragraph in assembled_body.split("\n\n") if paragraph.strip()]))
        candidate = DraftStory(title=pre_package.story.title, body=reversed_body, actual_word_count=calculate_word_count(reversed_body), scenes=[])

        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.stitch_scenes", return_value=candidate):
            package = _run_pipeline()
        self.assertEqual(package.story.body, assembled_body)
        self.assertIn("stitched_output_invalid; using assembled body", package.warnings)

    def test_kill_switch_disabled_still_invokes_stitcher(self):
        base_stub = stub_llm("friendship_and_feelings")
        prompts: list[str] = []

        def recording_stub(prompt, **kwargs):
            if kwargs.get("agent_name") == "scene_stitcher":
                prompts.append(prompt)
            return base_stub(prompt, **kwargs)

        with patch.object(model_client, "call_model_json", side_effect=recording_stub), patch.object(model_client, "call_model_tool", side_effect=recording_stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.SCENE_STITCHER_BYPASS_ENABLED", False), patch(
            "story_engine.pipeline.stitch_scenes", wraps=pipeline.stitch_scenes
        ) as stitched:
            _run_pipeline()
        self.assertEqual(stitched.call_count, 1)
        self.assertEqual(len(prompts), 1)
        stitch_failure = _stitch_failure_from_prompt(prompts[0])
        self.assertIn("legacy_full_boundary_pass", prompts[0])
        self.assertEqual(stitch_failure["boundary_indexes"], [1, 2, 3])

    def test_non_boundary_paragraph_edit_falls_back(self):
        base_stub = stub_llm("friendship_and_feelings")

        def scene_writer_override(prompt, **kwargs):
            payload = base_stub(prompt, **kwargs)
            if kwargs.get("scene_index") == 0:
                paragraphs = list(payload["paragraphs"])
                paragraphs[-1] = f'{paragraphs[-1]} Shared seam sentence.'
                return {"paragraphs": paragraphs}
            if kwargs.get("scene_index") == 1:
                paragraphs = list(payload["paragraphs"])
                paragraphs[0] = f"Shared seam sentence. {paragraphs[0]}"
                return {"paragraphs": paragraphs}
            return payload

        stub = stub_llm("friendship_and_feelings", scene_writer=scene_writer_override)
        assembled_bodies: list[str] = []

        def edited_non_boundary(blueprint, draft, stitch_failure):
            del stitch_failure
            assembled_bodies.append(draft.body)
            paragraphs = [paragraph for paragraph in draft.body.split("\n\n") if paragraph.strip()]
            paragraphs[3] = f"{paragraphs[3]} Changed away from the failed seam."
            body = "\n\n".join(paragraphs)
            return DraftStory(title=draft.title, body=body, actual_word_count=calculate_word_count(body), scenes=[])

        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch("story_engine.pipeline.stitch_scenes", side_effect=edited_non_boundary):
            package = _run_pipeline()
        self.assertEqual(package.story.body, assembled_bodies[0])
        self.assertIn("stitched_output_edited_non_boundary; using assembled body", package.warnings)

    def test_unparseable_seam_issues_skip_stitcher_and_warn(self):
        stub = stub_llm("friendship_and_feelings")
        forbidden = Mock(side_effect=AssertionError("stitcher should be skipped"))
        with patch.object(model_client, "call_model_json", side_effect=stub), patch.object(model_client, "call_model_tool", side_effect=stub), patch.object(
            model_client, "log_validator_decision", lambda **kw: None
        ), patch(
            "story_engine.checks.check_scene_seams",
            return_value={"ok": False, "severity": "failure", "issues": ["garbage_no_regex_match"], "route": "stitch"},
        ), patch("story_engine.pipeline.stitch_scenes", forbidden):
            package = _run_pipeline()
        forbidden.assert_not_called()
        self.assertEqual(_paragraph_count(package.story.body), 8)
        self.assertIn("seam_check_unparseable; stitcher skipped", package.warnings)
