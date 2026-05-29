from __future__ import annotations

import inspect
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, canonical_classification
from story_engine import pipeline
from story_engine.agents import judges
from story_engine.agents.polisher import _polish_offenders
from story_engine.config import AGENT_TEMPERATURES
from story_engine.prompts.language_judge import build_prompt
from story_engine.schemas import DraftStory, JudgeDecision, JudgeReport, RequestOptions


def _draft(body: str = "Sunny felt a sense of peace and accomplishment.\n\nThe soft, magical glow filled the meadow.") -> DraftStory:
    return DraftStory(title="Sunny Story", body=body, actual_word_count=len(body.split()), scenes=[])


def _eight_paragraph_draft() -> DraftStory:
    paragraphs = [f"Sunny paragraph {index} with concrete clover detail." for index in range(1, 9)]
    body = "\n\n".join(paragraphs)
    scenes = ["\n\n".join(paragraphs[index:index + 2]) for index in range(0, 8, 2)]
    return DraftStory(title="Sunny Story", body=body, actual_word_count=len(body.split()), scenes=scenes)


class _PostDraftReport:
    checks: dict = {}

    def to_dict(self) -> dict:
        return {"checks": self.checks}


def _pass_report(name: str) -> JudgeReport:
    return JudgeReport(judge_name=name, verdict="pass", reason=None, revision_guidance=None, fail_codes=[])


def _language_failure() -> JudgeReport:
    return judges._language_from_response(
        {
            "verdict": "fail",
            "failures": [
                {
                    "code": "abstract_language",
                    "evidence": "felt a sense of peace and accomplishment",
                    "revision_guidance": "Replace the abstract feeling summary with visible body action.",
                },
                {
                    "code": "generic_mood_words",
                    "evidence": "soft, magical glow",
                    "revision_guidance": "Use concrete objects from the scene.",
                },
            ],
        }
    )


class LanguageJudgeTests(unittest.TestCase):
    def test_prompt_signature_accepts_only_draft(self):
        parameters = inspect.signature(build_prompt).parameters
        self.assertEqual(list(parameters), ["draft"])

    def test_prompt_renders_draft_body_and_single_brace_json(self):
        draft = _draft("DRAFT BODY FOR PROMPT")
        prompt = build_prompt(draft)
        self.assertIn(draft.body, prompt)
        self.assertIn('{', prompt)
        self.assertIn('"verdict": "fail"', prompt)
        self.assertIn('}', prompt)
        self.assertNotIn('{{', prompt)
        self.assertNotIn('}}', prompt)

    def test_language_response_pass(self):
        report = judges._language_from_response({"verdict": "pass", "failures": []})
        self.assertEqual(report.judge_name, "language")
        self.assertEqual(report.verdict, "pass")
        self.assertEqual(report.reason, "")
        self.assertEqual(report.revision_guidance, "")
        self.assertEqual(report.fail_codes, [])

    def test_language_response_fail_rolls_up_evidence_and_guidance(self):
        report = _language_failure()
        self.assertEqual(report.judge_name, "language")
        self.assertEqual(report.verdict, "fail")
        for evidence in ["felt a sense of peace and accomplishment", "soft, magical glow"]:
            self.assertIn(f'"{evidence}"', report.reason)
            self.assertIn(f'"{evidence}"', report.revision_guidance)
        for code in ["abstract_language", "generic_mood_words"]:
            self.assertIn(code, report.revision_guidance)

    def test_polish_offenders_extracts_all_language_evidence(self):
        offenders = _polish_offenders(_language_failure())
        self.assertIn("felt a sense of peace and accomplishment", offenders)
        self.assertIn("soft, magical glow", offenders)

    def test_language_failure_reaches_pipeline_polish_without_scene_rewrite(self):
        language_report = _language_failure()
        classification = canonical_classification()
        blueprint = canonical_blueprint()
        draft = _eight_paragraph_draft()
        polish_calls = []
        rewrite_calls = []

        def polish_stub(draft_arg, failure_arg, blueprint_arg):
            polish_calls.append((draft_arg, failure_arg, blueprint_arg))
            return draft_arg

        with patch.object(pipeline, "understand", return_value={"classification": classification, "safety": SimpleNamespace(allowed=True)}), patch.object(
            pipeline, "plan_blueprint", return_value=blueprint
        ), patch.object(pipeline, "write_draft", return_value=draft), patch.object(
            pipeline, "_pre_stitch_scene_failures", return_value=[]
        ), patch.object(pipeline.checks, "check_scene_seams", return_value={"ok": True, "issues": []}), patch.object(
            pipeline.checks, "run_all", return_value=_PostDraftReport()
        ), patch.object(pipeline, "judge_safety", return_value=_pass_report("safety_judge")), patch.object(
            pipeline, "judge_coherence", return_value=_pass_report("coherence_judge")
        ), patch.object(pipeline, "judge_language", return_value=language_report), patch.object(
            pipeline, "polish", side_effect=polish_stub
        ), patch.object(pipeline, "rewrite_scene", side_effect=lambda *args, **kwargs: rewrite_calls.append((args, kwargs))), patch.object(
            pipeline, "_run_final_safety_gate", return_value=None
        ), patch.object(pipeline, "_apply_title", side_effect=lambda draft_arg, blueprint_arg: draft_arg):
            pipeline.run("gentle story", RequestOptions(story_mode="friendship", main_character_name="Sunny"))

        self.assertEqual(polish_calls[0][1], language_report)
        self.assertEqual(rewrite_calls, [])

    def test_language_failure_does_not_hard_reject(self):
        language_report = _language_failure()
        safety_report = _pass_report("safety_judge")
        coherence_report = _pass_report("coherence_judge")
        with patch.object(pipeline, "judge_safety", return_value=safety_report), patch.object(
            pipeline, "judge_coherence", return_value=coherence_report
        ), patch.object(pipeline, "judge_language", return_value=language_report):
            reports = pipeline.judge_all(_draft(), canonical_blueprint(), canonical_classification(), "request")
        self.assertEqual(reports[0], safety_report)
        self.assertEqual(reports[1], coherence_report)
        self.assertEqual(reports[2], language_report)

    def test_language_degraded_returns_pass_and_routes_nowhere(self):
        events: list[tuple[str, dict]] = []

        def fail_tool(*args, **kwargs):
            raise RuntimeError("tool unavailable")

        with patch.object(judges.model_client, "call_model_tool", side_effect=fail_tool), patch.object(
            judges, "trace_event", side_effect=lambda event_name, **kwargs: events.append((event_name, kwargs))
        ):
            report = judges.judge_language(_draft())

        self.assertEqual(report.judge_name, "language")
        self.assertEqual(report.verdict, "pass")
        self.assertEqual(report.reason, "")
        self.assertEqual(report.revision_guidance, "")
        self.assertEqual(pipeline._polish_failures([report], JudgeDecision(all_pass=True, failures=[], deterministic_failures=[], approved=True)), [])
        degraded = [event for event in events if event[1].get("event_type") == "degraded"]
        self.assertEqual(len(degraded), 1)
        self.assertEqual(degraded[0][0], "agents.judge")
        self.assertEqual(degraded[0][1]["judge_name"], "language")
        self.assertEqual(degraded[0][1]["reason"], "parse_or_tool_exhausted")
        self.assertIn("latency_ms", degraded[0][1])

    def test_language_success_emits_trace_event(self):
        events: list[tuple[str, dict]] = []
        with patch.object(judges.model_client, "call_model_tool", return_value={"verdict": "pass", "failures": []}), patch.object(
            judges, "trace_event", side_effect=lambda event_name, **kwargs: events.append((event_name, kwargs))
        ):
            report = judges.judge_language(_draft())

        self.assertEqual(report.verdict, "pass")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "agents.judge")
        self.assertEqual(events[0][1]["judge_name"], "language")
        self.assertEqual(events[0][1]["verdict"], "pass")
        self.assertFalse(events[0][1]["fallback"])
        self.assertIn("latency_ms", events[0][1])

    def test_language_evidence_internal_quotes_are_sanitized(self):
        report = judges._language_from_response(
            {
                "verdict": "fail",
                "failures": [
                    {
                        "code": "stiff_or_reported_dialogue",
                        "evidence": 'she said "hi" softly',
                        "revision_guidance": "Make the existing speech read naturally.",
                    }
                ],
            }
        )
        self.assertIn('"she said hi softly"', report.reason)
        self.assertIn("she said hi softly", _polish_offenders(report))

    def test_language_prompt_receives_only_draft_body_through_judge_all(self):
        body = "DRAFT_BODY_SHOULD_APPEAR in the story text."
        draft = _draft(body)
        blueprint = canonical_blueprint()
        blueprint.story_spine.central_problem = "CENTRAL_PROBLEM_SENTINEL_SHOULD_NOT_APPEAR"
        blueprint.story_spine.resolution = "RESOLUTION_SENTINEL_SHOULD_NOT_APPEAR"
        blueprint.story_spine.ending_image = "ENDING_IMAGE_SENTINEL_SHOULD_NOT_APPEAR"
        request = "REQUEST_SENTINEL_SHOULD_NOT_APPEAR"
        captured_prompts: list[str] = []

        def tool_response(prompt, **kwargs):
            agent_name = kwargs["agent_name"]
            if agent_name == "language_judge":
                captured_prompts.append(prompt)
                self.assertEqual(kwargs["temperature"], AGENT_TEMPERATURES["language_judge"])
                return {"verdict": "pass", "failures": []}
            if agent_name == "safety_judge":
                return {"judge_name": "safety_judge", "verdict": "pass", "reason": None, "revision_guidance": None}
            if agent_name == "coherence_judge":
                return {"passed": True, "fail_codes": []}
            raise AssertionError(f"unexpected agent_name: {agent_name}")

        with patch.object(judges.model_client, "call_model_tool", side_effect=tool_response):
            pipeline.judge_all(draft, blueprint, canonical_classification(), request)

        self.assertEqual(len(captured_prompts), 1)
        prompt = captured_prompts[0]
        self.assertIn(body, prompt)
        for sentinel in [
            request,
            blueprint.story_spine.central_problem,
            blueprint.story_spine.resolution,
            blueprint.story_spine.ending_image,
        ]:
            self.assertNotIn(sentinel, prompt)


if __name__ == "__main__":
    unittest.main()
