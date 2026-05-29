import json
import re
import unittest

from _helpers import canonical_blueprint, canonical_character_cards, canonical_classification
from story_engine.prompts import arc_planner, character_designer, classifier, coherence_judge, polish_language, polish_safety, safety_judge, scene_planner, scene_rewriter, scene_stitcher, scene_writer, title_writer
from story_engine.prompts.output_schema_examples import scene_card_example_for, story_spine_example_for
from story_engine.categories import CATEGORIES
from story_engine.schemas import DraftStory, JudgeReport, SceneCard, StorySpine


_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
_INPUT_SECTION_RE = re.compile(r"# Inputs(.*?)(?:\n# |\Z)", re.DOTALL)
_PYTHON_REPR_RE = re.compile(r"'[A-Za-z_][^']*':|:\s*(None|True|False)\b")


class PromptBuilderRenderTests(unittest.TestCase):
    def test_all_json_fences_parse(self):
        for prompt in self._rendered_prompts():
            for block in _JSON_BLOCK_RE.findall(prompt):
                with self.subTest(block=block[:40]):
                    json.loads(block)

    def test_rendered_prompts_do_not_include_python_repr_artifacts(self):
        for prompt in self._rendered_prompts():
            scan_regions = _JSON_BLOCK_RE.findall(prompt) + [match.group(1) for match in _INPUT_SECTION_RE.finditer(prompt)]
            scan_text = "\n".join(scan_regions)
            self.assertIsNone(_PYTHON_REPR_RE.search(scan_text))

    def test_output_schema_examples_round_trip_through_schemas(self):
        for category in CATEGORIES:
            category_id = category["id"]
            story_spine_payload = json.loads(story_spine_example_for(category_id))
            story_spine = StorySpine(**story_spine_payload)
            scene_cards_payload = json.loads(scene_card_example_for(category_id))["scene_cards"]
            scene_cards = [SceneCard(**payload) for payload in scene_cards_payload]
            self.assertEqual(story_spine.scene_count, 4)
            self.assertEqual(len(scene_cards), 4)

    def _rendered_prompts(self):
        classification = canonical_classification()
        blueprint = canonical_blueprint()
        card = blueprint.scene_cards[0]
        draft = DraftStory(title=blueprint.title, body="One.\n\nTwo.", actual_word_count=2, scenes=["One.\n\nTwo."])
        stitch_failure = {
            "boundary_indexes": [1],
            "seam_failures": [{"boundary_index": 1, "kind": "duplicate_adjacent_sentence", "evidence": "x"}],
            "expected_paragraph_count": 2,
        }
        failure = JudgeReport(
            judge_name="language",
            verdict="fail",
            reason="abstract wording",
            revision_guidance="replace the abstract wording with concrete action",
            fail_codes=[],
        )
        prompts = [
            classifier.build_prompt("a friendship story about Sunny", "auto_detect", CATEGORIES),
            character_designer.build_prompt(classification),
            arc_planner.build_prompt(classification, {"scene_count": 4, "paragraphs_per_scene": 2}, canonical_character_cards()),
            scene_planner.build_prompt(blueprint.story_spine, canonical_character_cards(), classification),
            scene_writer.build_prompt(blueprint, card, scene_role="opening", character_cards=canonical_character_cards()),
            scene_rewriter.build_prompt(
                card,
                failed_scene_text="broken text",
                fail_codes_with_evidence=[{"code": "missing_setting", "evidence": "x"}],
                character_cards=canonical_character_cards(),
            ),
            scene_stitcher.build_prompt(
                blueprint,
                draft.body,
                4,
                [{"scene_number": 1, "start_paragraph": 1, "end_paragraph": 2}],
                stitch_failure,
                2,
            ),
            title_writer.build_prompt(blueprint),
            coherence_judge.build_prompt(draft, blueprint, classification, classification.request_text),
            safety_judge.build_prompt(draft, blueprint, classification, classification.request_text),
            polish_language.build_prompt(draft, failure, blueprint),
            polish_safety.build_prompt(draft, failure, blueprint),
        ]
        return prompts
