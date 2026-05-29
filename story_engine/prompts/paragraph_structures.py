from typing import Any
import json


OPENING_APPENDIX = """- Position appendix: opening
- This is the opening scene.
- Paragraph 1 should establish the concrete setting, main character, and ordinary situation.
- Paragraph 2 must make the central problem child-clear through visible action, object evidence, or brief dialogue.
- Do not rely on subtle behavior alone to show what is wrong.
- Do not solve the problem yet.
"""

MIDDLE_APPENDIX = """- Position appendix: middle
- This is a middle scene.
- Show this scene as the next concrete step in the plan.
- Keep the action tied to this SceneCard's paragraph_beats.
- If dialogue is planned, place it near the must_show item it helps or responds to.
"""

CLOSING_APPENDIX = """- Position appendix: closing
- This is the closing scene.
- Show the final practical change or settling action from this SceneCard's paragraph_beats.
- Keep the main object, place, or resolved situation on-page.
- If scene_card.end_with is not null, end the second paragraph with scene_card.end_with exactly or with only tiny grammar changes.
- Do not add a moral, lesson, feeling summary, or extra sentence after scene_card.end_with.
- End with a concrete settling image, not a moral, lesson, or summary sentence.
"""


def position_appendix(role: str) -> str:
    if role == "opening":
        return OPENING_APPENDIX
    if role == "closing":
        return CLOSING_APPENDIX
    return MIDDLE_APPENDIX


PARAGRAPH_STRUCTURES_BY_CATEGORY = {
    "friendship_and_feelings": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Social Setup", "Small Social Problem"],
                "purpose": "Show a named shared activity, then make the character's social problem visible through action or a simple line.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["First Small Attempt", "Helper Notices"],
                "purpose": "Show one incomplete attempt to join or connect, then have a helper notice and offer one concrete next step.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Shared Inclusion Action", "Group Responds Kindly"],
                "purpose": "Show the character joining through one specific action, then show others making room, sharing, or responding kindly on-page.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Joined Activity Continues", "Shared Object or Place Settles"],
                "purpose": "Show the character taking part in the activity through one visible action, then end with the shared object, game space, or seating arrangement settled on-page.",
            },
        ],
    },

    "calm_educational_story": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Ordinary Observation", "Clear Question"],
                "purpose": "Show one visible household or nature phenomenon, then have the child ask one clear question about what they see.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["First Simple Explanation", "Safe Observation or Demonstration Setup"],
                "purpose": "Give one short concrete explanation, then set up one safe visible demonstration or observation.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Demonstration Happens", "Child Restates or Uses the Idea"],
                "purpose": "Show the concept happening visibly, then have the child name or use the idea in simple words.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Practical or Gentle Follow-Up", "Quiet Closing Image"],
                "purpose": "Show the child noticing the idea once more in the room or world, then close with the objects and room settling.",
            },
        ],
    },

    "cozy_animal_story": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Cozy Animal Setup", "Small Practical Problem"],
                "purpose": "Show the animal's small home or bedtime routine with concrete objects, then reveal a practical comfort or shelter problem.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["First Search or Repair Attempt", "Helper or Clue Appears"],
                "purpose": "Show one failed search or repair attempt, then introduce a useful helper or clue that changes what the animal can do next.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Shared Practical Action", "Problem Solved On-Page"],
                "purpose": "Show specific object-level fixing or finding actions, then prove the object or shelter problem is solved on-page.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Return to Comfort", "Solved Place Stays Settled"],
                "purpose": "Show the animal testing or returning to the repaired comfort, then end with the home safe, dry, quiet, or settled.",
            },
        ],
    },

    "general_bedtime_story": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Bedtime Routine Setup", "Small Bedtime Problem"],
                "purpose": "Show the familiar bedtime room and routine with concrete objects, then reveal one small ordinary thing that is not ready.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["First Fix", "Caregiver Helps"],
                "purpose": "Show the child beginning a practical fix, then a caregiver joins with one concrete helpful action.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Routine Continues", "Final Room Check"],
                "purpose": "Show the bedtime routine continuing after the fix, then check a few specific room objects into place.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Final Adjustment", "Room Objects Settle"],
                "purpose": "Show the child making one final bedtime adjustment, then end with the room objects, light, door, blanket, or toy in their final visible places.",
            },
        ],
    },

    "gentle_adventure": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Safe Errand or Small Mission", "Route Is Made Clear"],
                "purpose": "Introduce one small task close to home, then make the route clear with simple landmarks.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["First Landmark", "Small Obstacle or Careful Moment"],
                "purpose": "Show the character moving through the first landmark, then handling one gentle careful moment without danger.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Destination Reached", "Return Begins"],
                "purpose": "Show the errand, visit, or task completed on-page, then begin the return along the familiar route.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Home Comes Back Into View", "Calm Homecoming"],
                "purpose": "Show the character reaching home or the safe ending place, then end with the task complete and the character settled.",
            },
        ],
    },

    "magical_bedtime_story": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Ordinary Bedtime Setup", "Tiny Magical Sign"],
                "purpose": "Start with an ordinary bedtime routine or room problem, then introduce one tiny bounded magical sign.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["Careful Discovery", "Magic Has a Small Function"],
                "purpose": "Show the character investigating gently, then reveal the small useful thing the magic can do.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Character Acts", "Magic Quietly Finishes Its Job"],
                "purpose": "Show the child solving the problem through action, then show the magic dimming, settling, or becoming ordinary.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Return to Routine", "Small Magic Contained"],
                "purpose": "Show the child returning to bedtime routine, then end with the small magic quiet and contained in the room.",
            },
        ],
    },

    "silly_soft_story": {
        "scenes": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "functions": ["Ordinary Bedtime Setup", "Funny Small Problem"],
                "purpose": "Start with a normal bedtime task, then reveal one harmless visual mix-up with specific misplaced objects.",
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "functions": ["Character Notices or Reacts", "First Funny Fix"],
                "purpose": "Show a gentle funny reaction, then correct the first misplaced thing through a concrete action.",
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "functions": ["Second Funny Fix", "Final Check"],
                "purpose": "Correct another silly detail, then check the room or routine in a playful concrete list.",
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "functions": ["Last small Joke", "Calm Bedtime Landing"],
                "purpose": "Show one final small joke, then end with the corrected objects in place and the bedtime routine restored on-page.",
            },
        ],
    },
}

def paragraph_structure_for(category_id: str) -> dict:
    return PARAGRAPH_STRUCTURES_BY_CATEGORY.get(
        category_id,
        PARAGRAPH_STRUCTURES_BY_CATEGORY["general_bedtime_story"],
    )

def paragraph_structure_prompt_payload(category_id: str) -> str:
    """Return the selected category paragraph structure as JSON for prompt insertion."""
    return json.dumps(paragraph_structure_for(category_id), ensure_ascii=False)


SCENE_STRUCTURES_BY_CATEGORY = {
    "friendship_and_feelings": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the shared social setup, then show the small visible social problem",
                "paragraph_functions": ["Social Setup", "Small Social Problem"],
            },
            {
                "scene": 2,
                "purpose": "show the first small attempt, then show the helper noticing and responding concretely",
                "paragraph_functions": ["First Small Attempt", "Helper Notices"],
            },
            {
                "scene": 3,
                "purpose": "show the shared inclusion action, then show the group responding kindly",
                "paragraph_functions": ["Shared Inclusion Action", "Group Responds Kindly"],
            },
            {
                "scene": 4,
                "purpose": "show the emotional shift through behavior, then show a peaceful togetherness image",
                "paragraph_functions": ["Emotional Shift Shown Through Behavior", "Peaceful Togetherness Image"],
            },
        ]
    },

    "calm_educational_story": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the ordinary observation, then show the clear child question",
                "paragraph_functions": ["Ordinary Observation", "Clear Question"],
            },
            {
                "scene": 2,
                "purpose": "show the first simple explanation, then show the safe observation or demonstration setup",
                "paragraph_functions": ["First Simple Explanation", "Safe Observation or Demonstration Setup"],
            },
            {
                "scene": 3,
                "purpose": "show the demonstration happening, then show the child restating or using the idea",
                "paragraph_functions": ["Demonstration Happens", "Child Restates or Uses the Idea"],
            },
            {
                "scene": 4,
                "purpose": "show the practical or gentle follow-up, then show a quiet closing image",
                "paragraph_functions": ["Practical or Gentle Follow-Up", "Quiet Closing Image"],
            },
        ]
    },

    "cozy_animal_story": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the cozy animal setup, then show the small practical problem",
                "paragraph_functions": ["Cozy Animal Setup", "Small Practical Problem"],
            },
            {
                "scene": 2,
                "purpose": "show the first search or repair attempt, then show the helper or clue appearing",
                "paragraph_functions": ["First Search or Repair Attempt", "Helper or Clue Appears"],
            },
            {
                "scene": 3,
                "purpose": "show the shared practical action, then show the problem solved on-page",
                "paragraph_functions": ["Shared Practical Action", "Problem Solved On-Page"],
            },
            {
                "scene": 4,
                "purpose": "show the return to comfort, then show a restful nature image",
                "paragraph_functions": ["Return to Comfort", "Restful Nature Image"],
            },
        ]
    },

    "general_bedtime_story": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the bedtime routine setup, then show the small bedtime problem",
                "paragraph_functions": ["Bedtime Routine Setup", "Small Bedtime Problem"],
            },
            {
                "scene": 2,
                "purpose": "show the first fix, then show the caregiver helping with a concrete action",
                "paragraph_functions": ["First Fix", "Caregiver Helps"],
            },
            {
                "scene": 3,
                "purpose": "show the routine continuing, then show the final room check",
                "paragraph_functions": ["Routine Continues", "Final Room Check"],
            },
            {
                "scene": 4,
                "purpose": "show the settling action, then show a quiet lights-out image",
                "paragraph_functions": ["Settling Action", "Quiet Lights-Out Image"],
            },
        ]
    },

    "gentle_adventure": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the safe errand or small mission, then show the route being made clear",
                "paragraph_functions": ["Safe Errand or Small Mission", "Route Is Made Clear"],
            },
            {
                "scene": 2,
                "purpose": "show the first landmark, then show the small obstacle or careful moment",
                "paragraph_functions": ["First Landmark", "Small Obstacle or Careful Moment"],
            },
            {
                "scene": 3,
                "purpose": "show the destination reached, then show the return beginning",
                "paragraph_functions": ["Destination Reached", "Return Begins"],
            },
            {
                "scene": 4,
                "purpose": "show home coming back into view, then show the calm homecoming",
                "paragraph_functions": ["Home Comes Back Into View", "Calm Homecoming"],
            },
        ]
    },

    "magical_bedtime_story": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the ordinary bedtime setup, then show the tiny magical sign",
                "paragraph_functions": ["Ordinary Bedtime Setup", "Tiny Magical Sign"],
            },
            {
                "scene": 2,
                "purpose": "show the careful discovery, then show that the magic has a small function",
                "paragraph_functions": ["Careful Discovery", "Magic Has a Small Function"],
            },
            {
                "scene": 3,
                "purpose": "show the character acting, then show the magic quietly finishing its job",
                "paragraph_functions": ["Character Acts", "Magic Quietly Finishes Its Job"],
            },
            {
                "scene": 4,
                "purpose": "show the return to routine, then show the soft magical closing image",
                "paragraph_functions": ["Return to Routine", "Soft Magical Closing Image"],
            },
        ]
    },

    "silly_soft_story": {
        "scenes": [
            {
                "scene": 1,
                "purpose": "show the ordinary bedtime setup, then show the funny small problem",
                "paragraph_functions": ["Ordinary Bedtime Setup", "Funny Small Problem"],
            },
            {
                "scene": 2,
                "purpose": "show the character noticing or reacting, then show the first funny fix",
                "paragraph_functions": ["Character Notices or Reacts", "First Funny Fix"],
            },
            {
                "scene": 3,
                "purpose": "show the second funny fix, then show the final playful check",
                "paragraph_functions": ["Second Funny Fix", "Final Check"],
            },
            {
                "scene": 4,
                "purpose": "show the last soft joke, then show the calm bedtime landing",
                "paragraph_functions": ["Last Soft Joke", "Calm Bedtime Landing"],
            },
        ]
    },
}


def scene_structure_for(category_id: str) -> dict:
    return SCENE_STRUCTURES_BY_CATEGORY.get(
        category_id,
        SCENE_STRUCTURES_BY_CATEGORY["general_bedtime_story"],
    )

def scene_structure_prompt_payload(category_id: str) -> str:
    """Return the selected category scene structure as JSON for prompt insertion."""
    return json.dumps(scene_structure_for(category_id), ensure_ascii=False)


CHARACTER_GUIDES_BY_CATEGORY = {
    "general_bedtime_story": (
        "Use familiar everyday roles, such as child, sibling, parent, grandparent, neighbor, or pet. "
        "Give the main character one small concrete want or worry, plus a clear routine, object, or place when relevant. "
        "Speech should name small needs, ask simple questions, or notice the next step."
    ),

    "cozy_animal_story": (
        "Use small animal characters with animal-scale needs, such as fixing a nest, finding a dry spot, sharing food, "
        "preparing a den, or choosing a safe path. Use owned nests, dens, burrows, branches, ponds, or paths when relevant. "
        "Speech should name practical needs, useful materials, safe places, or small problems plainly."
    ),

    "gentle_adventure": (
        "Use characters suited to a safe errand, visit, search, delivery, or short trip. "
        "Give the main character a clear home/return anchor and a small concrete goal, not a grand quest. "
        "Support characters should guide, answer, carry, notice, or accompany. Speech should ask directions, notice clues, answer simply, or mark the next step."
    ),

    "magical_bedtime_story": (
        "Use characters connected to one small magical object, place, helper, or wonder, such as a glowing seed, moon button, tiny lantern, or sleepy star. "
        "Keep wants practical and small: return, mend, tuck away, light, find, share, or settle the magical thing. "
        "Speech should notice concrete magical details, ask what changed, or explain one small magical rule without sounding grand."
    ),

    "friendship_and_feelings": (
        "Use characters with clear social roles, such as friend, new friend, left-out child, helper, apologizer, includer, or listener. "
        "Give each character a small visible want or worry tied to sharing, joining, apologizing, making room, or being understood. "
        "Speech should invite, include, apologize, reassure, ask what is wrong, answer honestly, or name a simple feeling plainly."
    ),

    "silly_soft_story": (
        "Use characters suited to a harmless mix-up, funny object problem, mistaken routine, or gentle surprise. "
        "Give the main character a concrete silly problem to solve, not random goofiness. "
        "Support characters should notice the mix-up, try a simple fix, or react warmly. Speech may be surprised or lively, but should stay brief, kind, and tied to the action."
    ),

    "calm_educational_story": (
        "Use curious observers, practical helpers, or simple explainers. "
        "Give the main character a small concrete question or observation, and give the support character a reason to notice evidence or explain one simple cause-and-effect idea. "
        "Speech should ask practical questions, point to visible evidence, answer simply, or give one short concrete explanation without lecturing."
    ),
}

def character_guide_for(category_id: str) -> str:
    return CHARACTER_GUIDES_BY_CATEGORY.get(category_id, CHARACTER_GUIDES_BY_CATEGORY["general_bedtime_story"])

def character_cards_payload(character_cards: list[Any] | None) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for card in character_cards or []:
        if hasattr(card, "to_dict"):
            payload.append(card.to_dict())
        elif isinstance(card, dict):
            payload.append(card)
    return payload