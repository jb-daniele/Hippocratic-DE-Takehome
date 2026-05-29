from types import SimpleNamespace
import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, canonical_classification, varied_scene_paragraphs
from storynest_app.state import GENERIC_FAILURE_MESSAGE, message_for_failure
from story_engine import pipeline
from story_engine.errors import RunFailed
from story_engine.schemas import DraftStory, JudgeReport, RequestOptions


class _PostDraftReport:
    checks: dict = {}

    def to_dict(self) -> dict:
        return {"checks": self.checks}


def _draft(blueprint) -> DraftStory:
    scenes = []
    for index, card in enumerate(blueprint.scene_cards):
        payload = varied_scene_paragraphs(index, card)
        scenes.append("\n\n".join(payload["paragraphs"]))
    body = "\n\n".join(scenes)
    return DraftStory(title="Sunny Story", body=body, actual_word_count=len(body.split()), scenes=scenes)


def _pass_report(name: str) -> JudgeReport:
    return JudgeReport(judge_name=name, verdict="pass", reason=None, revision_guidance=None, fail_codes=[])


def _safety_fail() -> JudgeReport:
    return JudgeReport(
        judge_name="safety_judge",
        verdict="fail",
        reason="unsafe detail",
        revision_guidance="Remove the unsafe detail.",
        fail_codes=[],
    )


def _run_with_safety_reports(reports: list[JudgeReport]):
    classification = canonical_classification()
    blueprint = canonical_blueprint()
    draft = _draft(blueprint)

    with patch.object(pipeline, "understand", return_value={"classification": classification, "safety": SimpleNamespace(allowed=True)}), patch.object(
        pipeline, "plan_blueprint", return_value=blueprint
    ), patch.object(pipeline, "write_draft", return_value=draft), patch.object(
        pipeline, "_pre_stitch_scene_failures", return_value=[]
    ), patch.object(pipeline.checks, "check_scene_seams", return_value={"ok": True, "issues": []}), patch.object(
        pipeline.checks, "run_all", return_value=_PostDraftReport()
    ), patch.object(pipeline, "judge_safety", side_effect=reports), patch.object(
        pipeline, "judge_coherence", return_value=_pass_report("coherence_judge")
    ), patch.object(pipeline, "judge_language", return_value=_pass_report("language")), patch.object(
        pipeline, "polish", side_effect=lambda draft_arg, failure_arg, blueprint_arg: draft_arg
    ), patch.object(pipeline, "_run_final_safety_gate", return_value=None), patch.object(
        pipeline, "_apply_title", side_effect=lambda draft_arg, blueprint_arg: draft_arg
    ):
        return pipeline.run("gentle story", RequestOptions(story_mode="friendship", main_character_name="Sunny"))


class SafetyPolishOneAttemptTests(unittest.TestCase):
    def test_message_for_failure_maps_safety_and_generic(self):
        self.assertEqual(
            message_for_failure("safety_fail"),
            "Unable to generate a safe story with your request. Please try again!",
        )
        self.assertEqual(message_for_failure("paragraph_count_invalid"), GENERIC_FAILURE_MESSAGE)

    def test_safety_polish_succeeds_after_one_pass(self):
        package = _run_with_safety_reports([_safety_fail(), _pass_report("safety_judge")])

        self.assertTrue(package.approved)
        self.assertIsNotNone(package.story)

    def test_safety_polish_fails_after_one_pass(self):
        with self.assertRaises(RunFailed) as raised:
            _run_with_safety_reports([_safety_fail(), _safety_fail()])

        self.assertEqual(raised.exception.failure_category, "safety_fail")


if __name__ == "__main__":
    unittest.main()
