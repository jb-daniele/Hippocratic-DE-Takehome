import json

from story_engine.categories import CATEGORIES, STORY_MODE_TO_CATEGORY
from story_engine.prompts.output_schema_examples import STORY_SPINE_EXAMPLES_BY_CATEGORY
from story_engine.prompts.paragraph_structures import PARAGRAPH_STRUCTURES_BY_CATEGORY
from story_engine.schemas import CharacterCard, DialogueItem, MainCharacter, ParagraphBeat, RequestClassification, SceneCard, StoryBlueprint, StorySpine


class _FakeToolFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, name, arguments):
        self.function = _FakeToolFunction(name, arguments)


class _FakeMessage:
    def __init__(self, *, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, *, content=None, tool_calls=None):
        self.message = _FakeMessage(content=content, tool_calls=tool_calls)


class _FakeUsage:
    def __init__(self, *, prompt_tokens=None, completion_tokens=None):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeResponse:
    def __init__(self, *, content=None, tool_calls=None, prompt_tokens=None, completion_tokens=None):
        self.choices = [_FakeChoice(content=content, tool_calls=tool_calls)]
        self.usage = _FakeUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    def model_dump(self):
        tool_calls = self.choices[0].message.tool_calls
        return {
            "choices": [
                {
                    "message": {
                        "content": self.choices[0].message.content,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                }
                            }
                            for tool_call in (tool_calls or [])
                        ],
                    }
                }
            ],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
            },
        }

    def to_dict(self):
        return self.model_dump()


_DISPLAY_BY_CATEGORY = {category["id"]: category["display_name"] for category in CATEGORIES}
_MODE_BY_CATEGORY = {
    category_id: mode
    for mode, category_id in STORY_MODE_TO_CATEGORY.items()
    if category_id != "auto_detect"
}
_TITLE_BY_CATEGORY = {
    "friendship_and_feelings": "Sunny and the Clover Circle",
    "cozy_animal_story": "Sunny and the Leaf Roof",
}
_SPINE_TEMPLATES = {
    "friendship_and_feelings": {
        "story_premise": "Sunny Mole wants to join ring-tag after Lily Rabbit offers him an easy first turn.",
        "protagonist_name": "Sunny",
        "setting": "meadow clover patch in late afternoon",
        "central_problem": "Sunny wants to join ring-tag but stays behind the dandelion because the game looks too fast.",
        "resolution": "Sunny taps Lily's paw, joins the game, and the circle widens for him.",
        "ending_image": "Sunny rests beside Lily in the clover while his gray pebble sits in the quiet game circle.",
        "scene_count": 4,
        "scene_steps": [
            "Sunny watches ring-tag near the clover patch and stays outside the circle.",
            "Sunny takes one step toward the game, stops, and Lily offers an easy first turn.",
            "Sunny joins with one small action and the group makes room for him.",
            "Sunny laughs during one real turn and ends the game resting beside Lily.",
        ],
        "must_avoid": ["repeated reassurance", "abstract belonging language"],
    },
    "cozy_animal_story": {
        "story_premise": "Sunny Mole and Lily Rabbit patch a loose leaf roof before the evening drizzle reaches Sunny's bed.",
        "protagonist_name": "Sunny",
        "setting": "mossy burrow under the blackberry hedge",
        "central_problem": "A roof leaf has slipped aside and left a damp gap above Sunny's blanket.",
        "resolution": "Sunny and Lily press birch bark and dry leaves over the gap until the roof stays dry.",
        "ending_image": "Sunny curls beneath the patched roof while Lily watches the dry leaf settle over the burrow.",
        "scene_count": 4,
        "scene_steps": [
            "Sunny tidies the burrow and notices the leaf roof gap above his blanket.",
            "Sunny tries to fix the gap alone and Lily arrives with a firmer patch.",
            "Sunny and Lily fit the patch together and test that the burrow stays dry.",
            "Sunny settles under the repaired roof while the hedge rustles softly overhead.",
        ],
        "must_avoid": ["storm fear", "danger"],
    },
}


def _head_token(text):
    tokens = [token for token in str(text).lower().replace("-", " ").split() if token]
    for token in tokens:
        if token not in {"a", "an", "and", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with"}:
            return token
    return ""


def canonical_classification(category_id="friendship_and_feelings", main_character="Sunny"):
    return RequestClassification(
        request_text=f"a gentle {category_id} story about {main_character}",
        selected_story_mode=_MODE_BY_CATEGORY.get(category_id, "friendship"),
        main_character_name=main_character,
        category_id=category_id,
        category_display_name=_DISPLAY_BY_CATEGORY[category_id],
        classifier_confidence="high",
        classifier_rationale="test fixture",
        matched_signals=["user_selection"],
        fallback=False,
        classifier_skipped=True,
        main_characters=[MainCharacter(name=main_character, role="main")],
    )


def canonical_character_cards():
    return [
        CharacterCard(name="Sunny", pronouns="he/him", kind="mole", role="main character who wants to join ring-tag"),
        CharacterCard(name="Lily", pronouns="she/her", kind="rabbit", role="friend who notices and offers one easy first turn"),
    ]


def canonical_story_spine(category_id):
    payload = _SPINE_TEMPLATES.get(category_id)
    if payload is None:
        payload = STORY_SPINE_EXAMPLES_BY_CATEGORY[category_id]
    return StorySpine(**json.loads(json.dumps(payload)))


def canonical_scene_cards(category_id, spine):
    structures = PARAGRAPH_STRUCTURES_BY_CATEGORY[category_id]["scenes"]
    dialogues = [
        [DialogueItem(speaker="Sunny", purpose="quietly names why he is not joining")],
        [DialogueItem(speaker="Lily", purpose="offers an easy first turn")],
        [],
        [],
    ]
    beat_text = [
        [
            ["ring-tag whirls around clover stones", "gray pebble glints beside Sunny's shoe", "clover stems sway near Lily's paw"],
            ["Sunny starts forward past the dandelion", "dandelion screen hides Sunny's small paws", "fast game shows around the clover"],
        ],
        [
            ["Sunny steps closer beside the post", "Finch rushes past the clover marker", "Sunny returns edgeward by the stones"],
            ["Lily leaves the circle near Sunny", "Lily crouches nearby beside the pebble", "easy first tag waits between them"],
        ],
        [
            ["Lily lowers a paw toward Sunny", "Sunny taps gently on Lily's paw", "Finch calls counted from the path"],
            ["circle widens wider around Sunny's toes", "clover marker shifts beside the lane", "Sunny runs inside the open circle"],
        ],
        [
            ["Sunny laughs softly beside the pebble", "one real turn finishes near Lily", "gray pebble bobs in Sunny's paw"],
            ["Sunny rests beside Lily in clover", "quiet circle settles around the marker", "clover shade lingers over both friends"],
        ],
    ]
    cards = []
    for index, scene in enumerate(structures):
        cards.append(
            SceneCard(
                scene=index + 1,
                paragraphs=list(scene["paragraphs"]),
                setting=spine.setting if index == 0 else [
                    "edge of the ring-tag circle",
                    "clover ring-tag circle",
                    "quiet clover circle at dusk",
                ][index - 1],
                scene_change=spine.scene_steps[index],
                paragraph_beats=[
                    ParagraphBeat(paragraph=scene["paragraphs"][0], function=scene["functions"][0], must_show=beat_text[index][0]),
                    ParagraphBeat(paragraph=scene["paragraphs"][1], function=scene["functions"][1], must_show=beat_text[index][1]),
                ],
                dialogue=dialogues[index],
                end_with=spine.ending_image if index == 3 else None,
            )
        )
    return cards


def canonical_blueprint(category_id="friendship_and_feelings"):
    classification = canonical_classification(category_id=category_id)
    spine = canonical_story_spine(category_id)
    cards = canonical_scene_cards(category_id, spine)
    cast = canonical_character_cards()
    return StoryBlueprint(
        title=_TITLE_BY_CATEGORY.get(category_id, "Sunny and the Quiet Story"),
        category_id=category_id,
        category_display_name=classification.category_display_name,
        selected_story_mode=classification.selected_story_mode,
        main_characters=[classification.main_characters[0].name],
        character_cards=cast,
        scene_plan={"scene_count": 4, "paragraphs_per_scene": 2},
        story_spine=spine,
        scene_cards=cards,
    )


def varied_scene_paragraphs(scene_index, scene_card):
    speaker = scene_card.dialogue[0].speaker if scene_card.dialogue else None
    setting_token = _head_token(scene_card.setting)
    first_tokens = [_head_token(item) for item in scene_card.paragraph_beats[0].must_show]
    second_tokens = [_head_token(item) for item in scene_card.paragraph_beats[1].must_show]
    templates = [
        (
            f"{setting_token.title()} shadows stretched across the clover while Sunny nudged a brass spool with one paw. "
            f"{first_tokens[0].title()} looked lively from the grass, {first_tokens[1]} gleamed beside his shoe, and {first_tokens[2]} bent in the breeze. "
            "A ladybug paused on the dirt as he kept his place at the edge.",
            f"Sunny leaned toward the game, and {second_tokens[0]} began to show. "
            f"At once {second_tokens[1]} blocked his view, and {second_tokens[2]} stayed plain in his face."
            + (f' {speaker} said, "I can start with a tiny turn."' if speaker else "")
            + " He rubbed the spool with his thumb and waited.",
        ),
        (
            f"{setting_token.title()} dust lifted when Sunny counted three flat stones beside a birch ladder. "
            f"{first_tokens[0].title()} showed in his toes, {first_tokens[1]} flashed over the clover, and {first_tokens[2]} left him back by the post. "
            "He drew one slow circle in the dirt with the ladder tip.",
            f"Lily changed course, and {second_tokens[0]} became obvious before Sunny spoke. "
            f"Then {second_tokens[1]} brought her close, and {second_tokens[2]} gave the moment a gentle shape."
            + (f' {speaker} said, "You can try the easy part with me."' if speaker else "")
            + " Sunny nodded against the post.",
        ),
        (
            f"{setting_token.title()} color brightened when Lily balanced a paper lantern on the fence and Sunny stepped in. "
            f"{first_tokens[0].title()} happened first, {first_tokens[1]} followed on the next breath, and {first_tokens[2]} rang out from the path. "
            "Sunny lifted both heels as if the ground had made room for him.",
            f"Behind them, {second_tokens[0]} opened the lane. "
            f"A clover marker slid aside so {second_tokens[1]} stayed visible, and {second_tokens[2]} carried the game forward. "
            "The lantern swung once and went still.",
        ),
        (
            f"{setting_token.title()} hush settled over the grass while Sunny folded a ribbon around his wrist after the last run. "
            f"{first_tokens[0].title()} showed in his face, {first_tokens[1]} rested behind him, and {first_tokens[2]} bobbed near his shoe. "
            "He let out a breath that sounded almost like a song.",
            f"Near the quiet path, {second_tokens[0]} came softly into view, then {second_tokens[1]} held the last beat, and {second_tokens[2]} kept the circle calm. "
            f"{scene_card.end_with}" if scene_card.end_with is not None else "",
        ),
    ]
    paragraph_one, paragraph_two = templates[scene_index]
    return {"paragraphs": [paragraph_one, paragraph_two]}


def stub_llm(category_id, **overrides):
    blueprint = canonical_blueprint(category_id)
    classification = canonical_classification(category_id=category_id)
    cast = canonical_character_cards()
    written_scenes = {}

    def resolve(agent_key, default, *args, **kwargs):
        override = overrides.get(agent_key)
        if override is None:
            return default
        if callable(override):
            return override(*args, **kwargs)
        return override

    def side_effect(prompt, **kwargs):
        agent_name = kwargs.get("agent_name")
        scene_index = kwargs.get("scene_index")
        if agent_name == "classifier":
            return resolve(
                agent_name,
                {
                    "category_id": classification.category_id,
                    "confidence": "high",
                    "rationale": "test fixture",
                    "matched_signals": ["user_selection"],
                    "fallback": False,
                },
                prompt,
                **kwargs,
            )
        if agent_name == "character_designer":
            return resolve(agent_name, {"cast": [card.to_dict() for card in cast]}, prompt, **kwargs)
        if agent_name == "arc_planner":
            return resolve(agent_name, blueprint.story_spine.to_dict(), prompt, **kwargs)
        if agent_name == "scene_planner":
            return resolve(agent_name, {"scene_cards": [card.to_dict() for card in blueprint.scene_cards]}, prompt, **kwargs)
        if agent_name == "title_writer":
            return resolve(agent_name, {"title": blueprint.title}, prompt, **kwargs)
        if agent_name == "scene_writer":
            payload = varied_scene_paragraphs(scene_index, blueprint.scene_cards[scene_index])
            payload = resolve(agent_name, payload, prompt, **kwargs)
            if isinstance(payload, dict) and "paragraphs" in payload:
                written_scenes[scene_index] = "\n\n".join(payload["paragraphs"])
            return payload
        if agent_name == "scene_rewriter":
            default = varied_scene_paragraphs(0, blueprint.scene_cards[0])
            return resolve(
                agent_name,
                {"paragraphs": default["paragraphs"], "addresses_codes": ["missing_setting"]},
                prompt,
                **kwargs,
            )
        if agent_name == "scene_stitcher":
            ordered = [written_scenes[index] for index in sorted(written_scenes)]
            return resolve(agent_name, {"body": "\n\n".join(ordered)}, prompt, **kwargs)
        if agent_name == "safety_judge":
            return resolve(
                agent_name,
                {
                    "judge_name": "safety_judge",
                    "verdict": "pass",
                    "reason": None,
                    "revision_guidance": None,
                },
                prompt,
                **kwargs,
            )
        if agent_name == "coherence_judge":
            return resolve(agent_name, {"passed": True, "fail_codes": []}, prompt, **kwargs)
        if agent_name == "language_judge":
            return resolve(agent_name, {"verdict": "pass", "failures": []}, prompt, **kwargs)
        if agent_name == "polish":
            ordered = [written_scenes[index] for index in sorted(written_scenes)]
            return resolve(agent_name, {"body": "\n\n".join(ordered)}, prompt, **kwargs)
        raise AssertionError(f"Unexpected agent_name: {agent_name}")

    return side_effect
