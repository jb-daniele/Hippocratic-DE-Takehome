from typing import Any


FALLBACK_CATEGORY_ID = "general_bedtime_story"

CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "general_bedtime_story",
        "display_name": "General bedtime story",
        "description": "A calm, classic bedtime story for broad gentle requests.",
        "inclusion_signals": ["bedtime", "sleepy", "calm", "classic", "gentle story"],
        "exclusion_signals": ["school lesson", "facts about", "very silly", "quest"],
        "classifier_examples": [
            {
                "request": "A peaceful bedtime story about a child winding down.",
                "category": "general_bedtime_story",
                "reason": "The request asks for a broad calm bedtime story.",
            },
            {
                "request": "A classic sleepy story with a gentle goodnight ending.",
                "category": "general_bedtime_story",
                "reason": "The request is general, calm, and bedtime-focused.",
            }
        ],
        "writer_guidance": "Keep the scene quiet, familiar, and bedtime-centered. Use concrete room objects, simple routine actions, and visible bedtime progress instead of broad cozy language.",    },
    {
        "id": "cozy_animal_story",
        "display_name": "Cozy animal story",
        "description": "A snug story centered on friendly animals and comforting moments.",
        "inclusion_signals": ["animal", "cat", "dog", "bunny", "forest friends", "pet"],
        "exclusion_signals": ["scary predator", "animal facts lesson", "battle"],
        "classifier_examples": [
            {
                "request": "A story about a little fox finding a cozy den.",
                "category": "cozy_animal_story",
                "reason": "The animal lead and cozy goal are primary signals.",
            },
            {
                "request": "A sleepy otter loses his favorite rock before bed.",
                "category": "cozy_animal_story",
                "reason": "The request centers on an animal character in a gentle bedtime situation.",
            }
        ],
        "writer_guidance": "Keep the scene animal-scale and practical. Use small animal places, body actions, natural objects, and den/nest/burrow details, and show comfort through helping, fixing, finding, arranging, or settling action.",    },
    {
        "id": "gentle_adventure",
        "display_name": "Gentle adventure",
        "description": "A low-stakes journey with discovery, courage, and a safe return.",
        "inclusion_signals": ["adventure", "journey", "explore", "treasure", "quest"],
        "exclusion_signals": ["dangerous chase", "violence", "frightening peril"],
        "classifier_examples": [
            {
                "request": "A gentle adventure to find a lost glowing pebble.",
                "category": "gentle_adventure",
                "reason": "The request centers on a soft quest.",
            },
            {
                "request": "A child takes a safe moonlit walk to return a tiny lantern.",
                "category": "gentle_adventure",
                "reason": "The request includes a low-stakes journey and safe return.",
            }
        ],
        "writer_guidance": "Keep the outing low-stakes but engaging. Use clear landmarks, small discoveries, careful choices, and visible progress away from and back toward home.",    },
    {
        "id": "magical_bedtime_story",
        "display_name": "Magical bedtime story",
        "description": "A soothing bedtime story with wonder, magic, or enchanted settings.",
        "inclusion_signals": ["magic", "wizard", "fairy", "dragon", "enchanted", "spell"],
        "exclusion_signals": ["dark magic", "monster fight", "intense peril"],
        "classifier_examples": [
            {
                "request": "A magical bedtime story about a moonlit garden.",
                "category": "magical_bedtime_story",
                "reason": "Magic and bedtime calm are both explicit.",
            },
            {
                "request": "A kind fairy helps a star settle into the sky.",
                "category": "magical_bedtime_story",
                "reason": "The request uses gentle magical elements and soft wonder.",
            }
        ],
        "writer_guidance": "Keep the magic small, specific, and lightly whimsical. Let one magical detail gently change the bedtime routine while ordinary actions still carry the scene.",    },
    {
        "id": "friendship_and_feelings",
        "display_name": "Friendship and feelings",
        "description": "A story about kindness, friendship, confidence, or naming feelings.",
        "inclusion_signals": ["friend", "feelings", "sad", "nervous", "kindness", "sharing"],
        "exclusion_signals": ["lesson facts", "prank-only", "competitive conflict"],
        "classifier_examples": [
            {
                "request": "A story about two friends learning to share.",
                "category": "friendship_and_feelings",
                "reason": "The central topic is friendship and emotional learning.",
            },
            {
                "request": "A nervous child feels better after talking with a friend.",
                "category": "friendship_and_feelings",
                "reason": "The request focuses on feelings, reassurance, and friendship.",
            }
        ],
        "writer_guidance": "Show feelings through small social actions. Use concrete gestures like inviting, sharing, apologizing, waiting, making room, or trying again, and keep the emotional change visible but not over-explained.",    },
    {
        "id": "silly_soft_story",
        "display_name": "Silly soft story",
        "description": "A playful, funny story that stays gentle and bedtime-safe.",
        "inclusion_signals": ["silly", "funny", "goofy", "giggle", "ridiculous"],
        "exclusion_signals": ["mean prank", "gross-out", "chaotic yelling"],
        "classifier_examples": [
            {
                "request": "A silly story about pajamas that keep dancing.",
                "category": "silly_soft_story",
                "reason": "The request asks for gentle humor.",
            },
            {
                "request": "A goofy moon forgets where it put its slippers.",
                "category": "silly_soft_story",
                "reason": "The request is playful and funny without high stakes.",
            }
        ],
        "writer_guidance": "Keep the humor small, visual, and bedtime-safe. Use harmless mix-ups, silly object choices, or playful misunderstandings, then show the scene settling back toward ordinary bedtime order.",    },
    {
        "id": "calm_educational_story",
        "display_name": "Calm educational story",
        "description": "A quiet story that introduces simple facts or concepts without becoming a lesson.",
        "inclusion_signals": ["learn", "facts", "space", "ocean", "dinosaurs", "how does", "works", "explain"],
        "exclusion_signals": ["quiz", "worksheet", "complex lecture", "test prep"],
        "classifier_examples": [
            {
                "request": "A calm story that teaches a little about stars.",
                "category": "calm_educational_story",
                "reason": "The request asks for gentle learning content.",
            },
            {
                "request": "A bedtime story that explains how tide pools work.",
                "category": "calm_educational_story",
                "reason": "The request asks for quiet facts inside a story.",
            }
        ],
        "writer_guidance": "Keep the learning concrete and straightforward. Show one simple cause-and-effect idea through a visible observation, a short explanation, and the child using or restating the idea.",    },
]

STORY_MODE_TO_CATEGORY = {
    "auto_detect": "auto_detect",
    "classic": "general_bedtime_story",
    "animal": "cozy_animal_story",
    "gentle_adventure": "gentle_adventure",
    "magical": "magical_bedtime_story",
    "friendship": "friendship_and_feelings",
    "silly": "silly_soft_story",
    "educational": "calm_educational_story",
}
