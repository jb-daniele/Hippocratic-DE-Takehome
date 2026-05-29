import unittest

from story_engine.prompts.polish_language import (
    LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM,
    _select_examples_for_failure,
    build_prompt,
)


class FailureStub:
    def __init__(self, reason, revision_guidance):
        self.reason = reason
        self.revision_guidance = revision_guidance


class DraftStub:
    def __init__(self, body):
        self.body = body


class PolishLanguageExampleSelectionTests(unittest.TestCase):
    def test_reason_substring_selects_abstract_language_example(self):
        failure = FailureStub(reason="abstract_language: foo", revision_guidance="")

        self.assertEqual(
            _select_examples_for_failure(failure),
            LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["abstract_language"],
        )

    def test_guidance_substring_selects_generic_mood_words_example(self):
        failure = FailureStub(
            reason="",
            revision_guidance="please address generic_mood_words",
        )

        self.assertEqual(
            _select_examples_for_failure(failure),
            LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["generic_mood_words"],
        )

    def test_multiple_codes_select_in_dict_order(self):
        failure = FailureStub(
            reason="moralizing_ending detected",
            revision_guidance="also repetitive_openings",
        )
        expected = "\n\n".join(
            [
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["repetitive_openings"],
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["moralizing_ending"],
            ]
        )

        self.assertEqual(_select_examples_for_failure(failure), expected)

    def test_unknown_failure_text_falls_back_to_defaults(self):
        failure = FailureStub(
            reason="Language is too abstract.",
            revision_guidance="Use visible action.",
        )
        expected = "\n\n".join(
            [
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["abstract_language"],
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["generic_mood_words"],
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["quote_formatting"],
            ]
        )

        self.assertEqual(_select_examples_for_failure(failure), expected)

    def test_none_attributes_are_tolerated(self):
        failure = FailureStub(reason=None, revision_guidance=None)
        expected = "\n\n".join(
            [
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["abstract_language"],
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["generic_mood_words"],
                LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["quote_formatting"],
            ]
        )

        self.assertEqual(_select_examples_for_failure(failure), expected)

    def test_build_prompt_renders_without_syntax_error(self):
        import story_engine.prompts.polish_language as polish_language

        draft = DraftStub(body="The small fox curled up, feeling safe and content.")
        failure = FailureStub(reason="abstract_language: foo", revision_guidance="")

        prompt = polish_language.build_prompt(draft, failure, None)

        self.assertIsInstance(prompt, str)
        self.assertTrue(prompt)
        self.assertIn(
            LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["abstract_language"],
            prompt,
        )

    def test_prompt_post_final_check_prose_is_stable_across_selections(self):
        draft = DraftStub(body="Benny made room beside Rosie.")
        failure_a = FailureStub(
            reason="abstract_language: foo",
            revision_guidance="",
        )
        failure_b = FailureStub(
            reason="moralizing_ending detected",
            revision_guidance="",
        )

        prompt_a = build_prompt(draft, failure_a, None)
        prompt_b = build_prompt(draft, failure_b, None)

        post_a = "# Final Check" + prompt_a.split("# Final Check", 1)[1]
        post_b = "# Final Check" + prompt_b.split("# Final Check", 1)[1]

        self.assertEqual(post_a, post_b)
        # Sanity: the two renders genuinely differ somewhere (proving the
        # post-stability check isn't trivially true because the prompts
        # are identical).
        self.assertNotEqual(prompt_a, prompt_b)
        # And the difference lives in the examples block, not the post block.
        self.assertIn(
            LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["abstract_language"],
            prompt_a,
        )
        self.assertIn(
            LANGUAGE_POLISH_EXAMPLES_BY_PROBLEM["moralizing_ending"],
            prompt_b,
        )


if __name__ == "__main__":
    unittest.main()
