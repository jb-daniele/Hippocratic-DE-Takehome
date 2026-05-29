import unittest

from story_engine.pipeline.classify import _main_characters
from story_engine.schemas import RequestOptions


def _opts(name: str) -> RequestOptions:
    return RequestOptions(story_mode="friendship", main_character_name=name)


class MainCharacterNamesNormalizationTests(unittest.TestCase):
    def test_single_name_is_preserved(self):
        result = _main_characters(_opts("Sunny"))
        self.assertEqual([c.name for c in result], ["Sunny"])
        self.assertEqual([c.role for c in result], ["main"])

    def test_comma_separated_names_split_into_distinct_entries(self):
        result = _main_characters(_opts("Ella, Ben"))
        self.assertEqual([c.name for c in result], ["Ella", "Ben"])

    def test_extra_whitespace_and_empty_segments_dropped(self):
        result = _main_characters(_opts("  Ella ,, Ben ,  "))
        self.assertEqual([c.name for c in result], ["Ella", "Ben"])

    def test_empty_string_yields_no_characters(self):
        self.assertEqual(_main_characters(_opts("")), [])

    def test_dict_options_normalize_the_same_way(self):
        result = _main_characters({"story_mode": "friendship", "main_character_name": "Ella, Ben"})
        self.assertEqual([c.name for c in result], ["Ella", "Ben"])


if __name__ == "__main__":
    unittest.main()
