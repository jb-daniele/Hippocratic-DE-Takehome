import unittest

from story_engine.schemas import CharacterCard, SchemaError


class CharacterCardSchemaTests(unittest.TestCase):
    def test_constructs_with_four_fields(self):
        card = CharacterCard(name="Sunny", pronouns="he/him", kind="mole", role="main character")
        self.assertEqual(card.to_dict()["name"], "Sunny")

    def test_pronouns_must_be_supported(self):
        with self.assertRaises(SchemaError):
            CharacterCard(name="Sunny", pronouns="xe/xem", kind="mole", role="main character")

    def test_gender_property_derives_from_pronouns(self):
        self.assertEqual(CharacterCard(name="Lily", pronouns="she/her", kind="rabbit", role="friend").gender, "female")
        self.assertEqual(CharacterCard(name="Sunny", pronouns="he/him", kind="mole", role="main character").gender, "male")
        self.assertEqual(CharacterCard(name="Pip", pronouns="they/them", kind="finch", role="observer").gender, "neutral")

    def test_unknown_extra_field_raises(self):
        with self.assertRaises(SchemaError):
            CharacterCard(name="Sunny", pronouns="he/him", kind="mole", role="main character", color="brown")
