import unittest

from story_engine.agents import _speaker_match


class SpeakerMatchStrictTests(unittest.TestCase):
    def test_non_exact_name_does_not_match(self):
        self.assertIsNone(_speaker_match("Lila", ["Lily"]))

    def test_casefold_exact_name_matches(self):
        self.assertEqual(_speaker_match("lila", ["Lila"]), "Lila")
