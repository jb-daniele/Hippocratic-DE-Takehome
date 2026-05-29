import json


STORY_SPINE_EXAMPLES_BY_CATEGORY = {
    "friendship_and_feelings": {
        "story_premise": "Sunny Mole joins ring-tag after Lily gives him an easy first turn.",
        "protagonist_name": "Sunny",
        "setting": "meadow clover patch in late afternoon",
        "central_problem": "Sunny wants to join ring-tag but stays behind the dandelion because the game looks too fast.",
        "resolution": "Sunny taps Lily's paw, joins the game, and the animals widen the clover circle for him.",
        "ending_image": "Sunny rests beside Lily in the clover while his gray pebble sits in the quiet game circle.",
        "scene_count": 4,
        "scene_steps": [
            "Sunny watches the meadow animals play ring-tag near the clover patch, then stays behind a dandelion because the game looks too fast",
            "Sunny takes two small steps toward the circle but stops when Finch swoops past, then Lily leaves the game and offers him an easy first tag",
            "Sunny taps Lily's paw, then the animals widen the clover circle so Sunny has room to run",
            "Sunny runs one real turn and laughs during the game, then rests beside Lily while his gray pebble sits in the quiet circle",
        ],
        "must_avoid": [
            "repeated reassurance",
            "abstract belonging language",
            "loud chaos",
            "danger",
        ],
    },

    "calm_educational_story": {
        "story_premise": "Nora learns where steam goes by watching it turn back into water drops on a cool spoon.",
        "protagonist_name": "Nora",
        "setting": "kitchen table beside the sink",
        "central_problem": "Nora sees steam disappear above Dad's mug and asks where the water goes when she cannot see it anymore.",
        "resolution": "Tiny drops gather on the cold spoon above the mug, and Nora says the steam turned back into water.",
        "ending_image": "Nora leans against Dad while the empty mug sits by the sink and the dry spoon rests beside the folded napkin.",
        "scene_count": 4,
        "scene_steps": [
            "Nora watches steam curl from Dad's blue mug, then asks where the steam goes when it disappears",
            "Dad explains that warm water can rise as steam, then holds a chilled spoon safely above the mug",
            "Tiny drops gather on the underside of the spoon, then Nora says the steam turned back into water drops",
            "Nora notices fog from her breath on the window, then leans against Dad while the mug and spoon rest quietly by the sink",
        ],
        "must_avoid": [
            "lecture-like explanation",
            "unsafe touching of hot objects",
            "abstract wonder language",
            "messy demonstration",
        ],
    },

    "cozy_animal_story": {
        "story_premise": "Milo Mouse repairs the loose leaf roof of his burrow with Junie Snail before the rain comes in.",
        "protagonist_name": "Milo",
        "setting": "little burrow beneath the blackberry hedge",
        "central_problem": "A dry leaf falls from Milo's burrow roof and leaves a small open patch where rain could drip through.",
        "resolution": "Milo and Junie press birch bark and dry oak leaves into the gap until the roof stays covered and dry.",
        "ending_image": "Milo rests under his patched leaf roof while rain pats the blackberry leaves outside and no drops come through.",
        "scene_count": 4,
        "scene_steps": [
            "Milo tidies his burrow for bed, then a roof leaf slips down and shows a rain gap above his nest",
            "Milo tries to press leaves back into the hole but they fall down, then Junie Snail arrives with birch bark and notices the roof needs a stiff patch",
            "Milo holds the birch bark while Junie presses oak leaves into place, then Milo taps the mended roof and no drops come through",
            "Milo sets his thimble cup back on its stone and tucks in, then rain pats outside while the patched roof stays dry",
        ],
        "must_avoid": [
            "storm fear",
            "danger",
            "generic teamwork language",
            "scary animals",
        ],
    },

    "general_bedtime_story": {
        "story_premise": "Lena gets Bear ready for bed by cleaning him, changing his sweater, and settling the room.",
        "protagonist_name": "Lena",
        "setting": "Lena's bedroom at bedtime",
        "central_problem": "Bear is still wearing his daytime sweater and has a dried jam spot on his chin.",
        "resolution": "Lena and Mom clean Bear, fold his sweater, and tuck him into his blue sleep sack.",
        "ending_image": "Lena holds Bear's paw in bed while the hallway light glows under the door and the small square of sky stays still.",
        "scene_count": 4,
        "scene_steps": [
            "Lena finishes her bedtime routine and reaches for Bear, then notices he is still wearing his daytime sweater with jam on his chin",
            "Lena wipes Bear's chin and tries to fix the sweater, then Mom comes in and helps find Bear's sleep sack",
            "Lena and Mom tuck Bear into the blue sleep sack, then Lena checks the cup, socks, book, curtain, slipper, and closet door",
            "Lena climbs into bed with Bear and listens to the moon book, then the hallway light clicks off while her hand stays curled around Bear's paw",
        ],
        "must_avoid": [
            "plot escalation",
            "magical event",
            "abstract comfort language",
            "new bedtime problem at the end",
        ],
    },

    "gentle_adventure": {
        "story_premise": "Suri returns Mrs. Vale's basket before pajama time by following the garden route there and back.",
        "protagonist_name": "Suri",
        "setting": "quiet garden path between Suri's porch and Mrs. Vale's back step",
        "central_problem": "Suri needs to return Mrs. Vale's empty willow basket before pajama time.",
        "resolution": "Suri gives the willow basket back to Mrs. Vale and follows the same garden route home.",
        "ending_image": "Suri stands inside while the basket's empty spot on the kitchen bench looks tidy and the blue gate rests still in the dim garden.",
        "scene_count": 4,
        "scene_steps": [
            "Suri finds Mrs. Vale's empty willow basket on the kitchen bench, then Dad gives her the route past the bean rows, shed, blue gate, and back step",
            "Suri counts the stepping stones between the bean rows and steps around a snail, then carefully frees the basket handle from a low plum branch",
            "Suri slips through the blue gate and gives the basket to Mrs. Vale, then starts home along the same garden path",
            "Suri sees Dad waiting on the porch and retraces the route out loud, then steps inside while the garden smell drifts in and the blue gate rests still",
        ],
        "must_avoid": [
            "treasure hunt",
            "caves or secrets",
            "dangerous obstacle",
            "unresolved adventure hook",
        ],
    },

    "magical_bedtime_story": {
        "story_premise": "Lumi finds her missing silver bookmark after a tiny star of light points toward it before bed.",
        "protagonist_name": "Lumi",
        "setting": "Lumi's bedroom at bedtime",
        "central_problem": "Lumi's silver ribbon bookmark is missing from her moon book before bed.",
        "resolution": "Lumi follows the star's light, reaches behind the bed with her hairbrush, and pulls the silver bookmark free.",
        "ending_image": "Lumi rests under her quilt while the silver bookmark lies inside the closed moon book and the tiny stitched star glimmers once beside her pillow.",
        "scene_count": 4,
        "scene_steps": [
            "Lumi gets ready for bed and looks through her moon book, then notices the silver ribbon bookmark is missing",
            "A tiny star-shaped glow appears by her pillow, then Lumi lifts the pillow and sees the star point toward the side of the bed",
            "Lumi follows the silver stripe to the bookmark behind the bed leg, then uses her hairbrush handle to pull the ribbon free",
            "Lumi puts the bookmark back inside the moon book and climbs under the quilt, then the tiny star becomes a quiet stitch beside her pillow",
        ],
        "must_avoid": [
            "large magical quest",
            "magic solving everything alone",
            "scary mystery",
            "unbounded magical world",
        ],
    },

    "silly_soft_story": {
        "story_premise": "Tessa fixes a silly bedtime mix-up after dressing the room instead of herself.",
        "protagonist_name": "Tessa",
        "setting": "Tessa's bedroom after bath time",
        "central_problem": "Tessa's pajama shirt is on the lamp and her slippers are in the wrong places instead of being ready for bed.",
        "resolution": "Tessa puts on the pajama shirt, returns both slippers beside the bed, and checks that the room is properly undressed.",
        "ending_image": "Tessa smiles into her pillow while her pajama shirt stays on her, the slippers rest together, and the lamp stands bare in the dark room.",
        "scene_count": 4,
        "scene_steps": [
            "Tessa starts bedtime with pajamas on the bed, then Dad returns to find the shirt on the lamp and the slippers out of place",
            "Dad asks if Tessa dressed the room instead of herself, then Tessa takes the pajama shirt off the lamp and puts it on",
            "Tessa rescues the slipper from the windowsill and Dad finds the other under the rug, then they check that the shirt, lamp, slippers, rug, and pillow are right",
            "Tessa asks whether her toes need hats and gets tucked in, then the lamp clicks off while the shirt, slippers, and room stay settled",
        ],
        "must_avoid": [
            "chaotic escalation",
            "mean teasing",
            "gross-out humor",
            "delaying bedtime too much",
        ],
    },
}

def story_spine_example_for(category_id: str) -> str:
    example = STORY_SPINE_EXAMPLES_BY_CATEGORY.get(
        category_id,
        STORY_SPINE_EXAMPLES_BY_CATEGORY["general_bedtime_story"],
    )
    return json.dumps(example, ensure_ascii=False, indent=2)



SCENE_CARD_EXAMPLES_BY_CATEGORY = {
    "friendship_and_feelings": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "meadow clover patch in late afternoon",
                "scene_change": "Sunny watches ring-tag from the edge, then hides because the game looks too fast.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Social Setup",
                        "must_show": [
                            "Lily, Finch, and Squirrel play ring-tag around the clover patch",
                            "Sunny sits at the edge holding a smooth gray pebble in both paws",
                            "the game moves from stump to stone to tall grass stems",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Small Social Problem",
                        "must_show": [
                            "Sunny opens his mouth when Lily runs close, then shuts it",
                            "Sunny shuffles behind a tall dandelion stalk",
                            "Sunny rubs one paw over the pebble and whispers that he will get in the way",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Sunny",
                        "purpose": "quietly names why he is not joining",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "edge of the ring-tag circle",
                "scene_change": "Sunny makes one small attempt, then Lily offers him an easy first turn.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "First Small Attempt",
                        "must_show": [
                            "Sunny takes two small steps toward the ring-tag circle",
                            "Finch swoops past and Squirrel zips behind a buttercup",
                            "Sunny backs up to the dandelion and looks down at his pebble",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Helper Notices",
                        "must_show": [
                            "Lily slows when she sees Sunny standing by himself",
                            "Lily hops out of the game and comes to Sunny's side",
                            "Lily holds out one paw and stands still for an easy first tag",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Lily",
                        "purpose": "offers an easy first turn",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "clover ring-tag circle",
                "scene_change": "Sunny tags Lily, and the group changes the circle so he can play.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Shared Inclusion Action",
                        "must_show": [
                            "Sunny reaches out slowly and taps Lily's paw",
                            "Sunny says tag very quietly",
                            "Lily springs away and tells the others Sunny tagged her",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Group Responds Kindly",
                        "must_show": [
                            "Finch lands on the low stump and suggests making the circle wider",
                            "Squirrel pushes two fallen leaves out of the way",
                            "Lily runs past Sunny slowly enough for him to reach",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Sunny",
                        "purpose": "names the joining action after doing it",
                    },
                    {
                        "speaker": "Lily",
                        "purpose": "responds that the action counted",
                    },
                ],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "quiet clover patch after the game",
                "scene_change": "Sunny plays a real turn, then rests with Lily and the group.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Emotional Shift Shown Through Behavior",
                        "must_show": [
                            "Sunny's paws move faster over the grass",
                            "Sunny laughs when Squirrel peeks from behind a daisy",
                            "Sunny's gray pebble slips from his paws and bounces into the clover",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Peaceful Togetherness Image",
                        "must_show": [
                            "the animals flop down together in the cool grass",
                            "Lily settles beside Sunny near the dandelion",
                            "Sunny's gray pebble rests in the middle of the quiet clover circle",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": "Sunny rests beside Lily in the clover while his gray pebble sits in the quiet game circle.",
            },
        ],
    },

    "calm_educational_story": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "kitchen table beside the sink",
                "scene_change": "Nora sees steam rise from Dad's mug and asks where it goes.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Ordinary Observation",
                        "must_show": [
                            "Dad pours warm tea into his blue mug at the kitchen table",
                            "a pale ribbon of steam curls above the cup and fades",
                            "one cloudy patch appears on the window over the sink",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Clear Question",
                        "must_show": [
                            "Nora points at the steam above the mug",
                            "Nora asks where the steam goes when she cannot see it",
                            "Dad sets the kettle safely on the back of the counter",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Nora",
                        "purpose": "asks where the steam goes",
                    },
                    {
                        "speaker": "Dad",
                        "purpose": "acknowledges the question as something they can observe safely",
                    },
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "kitchen table near Dad's mug",
                "scene_change": "Dad explains steam simply and prepares a cold spoon observation.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "First Simple Explanation",
                        "must_show": [
                            "Dad points to the warm tea while steam lifts from the mug",
                            "Dad explains that tiny bits of water float up as steam",
                            "Nora watches the wispy curls lift and disappear",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Safe Observation or Demonstration Setup",
                        "must_show": [
                            "Dad presses a clean metal spoon against the cool window",
                            "Dad holds the spoon by the handle above the steam",
                            "Nora watches the spoon without touching the hot mug",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Dad",
                        "purpose": "gives a short cause-and-effect explanation",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "kitchen table above the mug",
                "scene_change": "Tiny water drops form on the cold spoon, and Nora explains what happened.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Demonstration Happens",
                        "must_show": [
                            "steam brushes the underside of the cold spoon",
                            "tiny drops gather on the spoon like pinpricks",
                            "one clear bead slides to the spoon's edge",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Child Restates or Uses the Idea",
                        "must_show": [
                            "Nora points to the water beads on the spoon",
                            "Nora says the steam touched the cold spoon and turned back into water",
                            "Dad lowers the spoon onto a folded napkin",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Nora",
                        "purpose": "states the idea in simple words after seeing the result",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "quiet kitchen by the window and sink",
                "scene_change": "Nora notices the idea on the window, then the kitchen is cleared and quiet.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Practical or Gentle Follow-Up",
                        "must_show": [
                            "Nora breathes softly on the kitchen window",
                            "a foggy circle blooms on the glass",
                            "Nora draws a tiny moon in the fog and names the little drops",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Quiet Closing Image",
                        "must_show": [
                            "Dad carries the empty mug to the sink",
                            "Nora wipes the tiny moon from the window with a dish towel",
                            "the dry spoon rests beside the folded napkin",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Nora",
                        "purpose": "notices the idea happening again",
                    }
                ],
                "end_with": "Nora leans against Dad while the empty mug sits by the sink and the dry spoon rests beside the folded napkin.",
            },
        ],
    },

        "cozy_animal_story": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "little burrow beneath the blackberry hedge",
                "scene_change": "Milo's snug burrow is ready for bed, then a loose roof leaf opens a small gap.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Cozy Animal Setup",
                        "must_show": [
                            "Milo sweeps the burrow doorway with a fern stem",
                            "his thimble cup sits on a flat gray stone beside the bed",
                            "Milo taps the leaf roof once before climbing into his nest",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Small Practical Problem",
                        "must_show": [
                            "one dry leaf slips loose and lands on Milo's nose",
                            "Milo sees a small open patch of sky between two roots",
                            "a cool breeze makes the red thread blanket flutter",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Milo",
                        "purpose": "names the practical problem with the roof",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "inside Milo's burrow under the roof gap",
                "scene_change": "Milo's leaf patch falls twice, then Junie brings stiff bark for the repair.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "First Search or Repair Attempt",
                        "must_show": [
                            "Milo stands on the flat stone and presses the leaf toward the gap",
                            "the leaf bends in the middle and floats down again",
                            "a wider leaf turns sideways and lands on the thimble cup",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Helper or Clue Appears",
                        "must_show": [
                            "Junie Snail slides in with a curled strip of birch bark on her shell",
                            "Junie touches the loose roof leaves with one feeler",
                            "Junie says the flat patch needs something stiff behind it",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Junie",
                        "purpose": "notices why the first fix is not working",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "Milo's burrow beneath the roof gap",
                "scene_change": "Milo and Junie patch the roof, and no drops come through when they test it.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Shared Practical Action",
                        "must_show": [
                            "Junie nudges the birch bark between the roots",
                            "Milo holds the bark steady with the fern stem",
                            "Milo tucks dry oak leaves over the bark like shingles",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Problem Solved On-Page",
                        "must_show": [
                            "the open patch disappears under the oak leaves",
                            "Milo taps the mended roof twice",
                            "Junie shakes the doorway vine and no drops fall through",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "dry burrow doorway during soft rain",
                "scene_change": "Milo puts the burrow back in order, and the patched roof stays dry in the rain.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Return to Comfort",
                        "must_show": [
                            "Milo lifts the leaf hat off the thimble cup",
                            "Milo sets the cup neatly back on its flat stone",
                            "Milo tucks the red thread blanket around his paws",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Restful Nature Image",
                        "must_show": [
                            "rain pats softly on the blackberry leaves outside",
                            "the birch bark holds the oak leaves firm between the roots",
                            "Junie rests by the doorway while Milo's blanket stays dry",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Milo",
                        "purpose": "notices the repaired space feels or sounds right",
                    }
                ],
                "end_with": "Milo rests under his patched leaf roof while rain pats the blackberry leaves outside and no drops come through.",
            },
        ],
    },

        "general_bedtime_story": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "Lena's bedroom at bedtime",
                "scene_change": "Lena has finished most bedtime tasks, then sees that Bear is not ready for bed.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Bedtime Routine Setup",
                        "must_show": [
                            "Lena sets the moon book beside the lamp after brushing her teeth",
                            "the curtain stays open one finger-width with a dark blue square of sky showing",
                            "Bear waits against the pillow with his round ears tilted",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Small Bedtime Problem",
                        "must_show": [
                            "Lena lifts Bear and sees his yellow daytime sweater",
                            "a dried jam spot sits on Bear's chin",
                            "Lena says Bear cannot sleep in his outside sweater",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Lena",
                        "purpose": "names why Bear is not ready for bed",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "little table beside Lena's bed",
                "scene_change": "Lena cleans Bear's chin, and Mom finds the sleep sack for the next step.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "First Fix",
                        "must_show": [
                            "Lena carries Bear to the little table beside the bed",
                            "Lena wipes the jam spot with a damp corner of the washcloth",
                            "Bear's sweater bunches around his middle when Lena tugs one sleeve",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Caregiver Helps",
                        "must_show": [
                            "Mom sets the laundry basket down by the doorway",
                            "Mom opens the bottom drawer and finds Bear's blue sleep sack",
                            "Lena holds Bear steady while Mom folds the yellow sweater",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Mom",
                        "purpose": "offers the next practical step",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "Lena's bed and bedroom floor",
                "scene_change": "Bear is dressed for bed, and Lena checks the room into place.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Routine Continues",
                        "must_show": [
                            "Lena guides Bear's feet into the blue sleep sack",
                            "Mom fastens the white button while Lena smooths Bear's ears",
                            "Lena tucks the moon book beside Bear with the silver picture facing up",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Final Room Check",
                        "must_show": [
                            "Lena points to the water cup, socks, book, and curtain",
                            "Lena nudges one stray slipper under the chair",
                            "Mom pushes the closet door until it clicks shut",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Lena",
                        "purpose": "checks the room objects into place",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "Lena's bed after lights-out",
                "scene_change": "Lena and Bear settle under the blanket, and the room becomes still.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Settling Action",
                        "must_show": [
                            "Lena climbs into bed and tucks Bear against her shoulder",
                            "Lena pulls the blanket over Bear's paws before covering her own knees",
                            "Mom reads the first two pages of the moon book in a low voice",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Quiet Lights-Out Image",
                        "must_show": [
                            "Mom sets the moon book on the table and clicks off the hallway light",
                            "Bear's clean chin rests above the blue sleep sack",
                            "Lena's hand stays curled around Bear's paw",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": "Lena holds Bear's paw in bed while the hallway light glows under the door and the small square of sky stays still.",
            },
        ],
    },

    "gentle_adventure": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "Suri's kitchen bench and porch after supper",
                "scene_change": "Suri finds the basket and learns the safe route to return it.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Safe Errand or Small Mission",
                        "must_show": [
                            "Suri finds Mrs. Vale's small willow basket on the kitchen bench",
                            "the folded cloth sits inside the empty basket",
                            "Suri lifts the basket handle and says she can return it before pajama time",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Route Is Made Clear",
                        "must_show": [
                            "Dad stands on the porch and points past the bean rows",
                            "Suri repeats the route: bean rows, shed, blue gate, back step",
                            "Dad stays on the porch where Suri can still see him",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Dad",
                        "purpose": "gives the simple route",
                    },
                    {
                        "speaker": "Suri",
                        "purpose": "repeats the route back",
                    },
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "garden path between the bean rows and shed",
                "scene_change": "Suri follows the route and handles the snagged basket carefully.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "First Landmark",
                        "must_show": [
                            "Suri walks between the bean rows and counts the stepping stones",
                            "a snail crosses the next stone",
                            "Suri steps around the snail and shifts the basket onto her hip",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Small Obstacle or Careful Moment",
                        "must_show": [
                            "the basket handle snags on a low plum branch",
                            "Suri holds the handle steady instead of yanking it",
                            "Suri bends the branch down until the basket slips free",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "Mrs. Vale's back step and the garden path home",
                "scene_change": "Suri gives back the basket and starts home by the same route.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Destination Reached",
                        "must_show": [
                            "Suri slips through the blue gate",
                            "Mrs. Vale stands on her back step with a tea towel",
                            "Suri holds out the willow basket with both hands",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Return Begins",
                        "must_show": [
                            "Suri turns back toward the garden path",
                            "the shed comes before the bean rows on the way home",
                            "Suri ducks under the plum branch before the basket handle can catch",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Suri",
                        "purpose": "politely completes the errand",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "Suri's porch and kitchen doorway",
                "scene_change": "Suri returns to Dad and the completed errand settles into bedtime.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Home Comes Back Into View",
                        "must_show": [
                            "Dad lifts one hand from the porch rail when Suri comes back into view",
                            "Suri calls the route back softly: bean rows, shed, blue gate, back home",
                            "Suri brushes one bit of garden dirt from her shoe on the porch step",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Calm Homecoming",
                        "must_show": [
                            "Dad pulls the kitchen door shut behind Suri",
                            "the empty spot on the kitchen bench looks tidy",
                            "Dad lays Suri's pajamas over the chair by the warm stove",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Suri",
                        "purpose": "softly marks that she has returned home",
                    }
                ],
                "end_with": "Suri stands inside while the basket's empty spot on the kitchen bench looks tidy and the blue gate rests still in the dim garden.",
            },
        ],
    },

        "magical_bedtime_story": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "Lumi's bedroom at bedtime",
                "scene_change": "The silver bookmark is missing, and a tiny star-shaped glow points away from the pillow.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Ordinary Bedtime Setup",
                        "must_show": [
                            "Lumi stacks her picture books beside the lamp",
                            "Lumi sees that the silver ribbon bookmark is not inside the moon book",
                            "the blue quilt, sock basket, and bedside lamp place the search in her bedroom",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Tiny Magical Sign",
                        "must_show": [
                            "a star-shaped glow no bigger than a coat button blinks at the edge of Lumi's pillow",
                            "Lumi lifts the pillow and sees the tiny star lying flat underneath",
                            "one point of the star tips toward the side of the bed",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "floor beside Lumi's bed",
                "scene_change": "Lumi learns that the small star can point to the missing bookmark.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "Careful Discovery",
                        "must_show": [
                            "the star stays flat and quiet instead of flying or making noise",
                            "Lumi leans close to watch the tipped star point",
                            "a faint silver stripe stretches from the star across the floorboards",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "Magic Has a Small Function",
                        "must_show": [
                            "Lumi follows the silver stripe with her eyes to the bed leg",
                            "a curl of silver ribbon shows in the shadow under the wooden rail",
                            "Lumi whispers that the star found her bookmark",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Lumi",
                        "purpose": "notices that the star has found the bookmark",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "rug beside Lumi's bed",
                "scene_change": "Lumi pulls the bookmark free, and the star becomes an ordinary stitch.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Character Acts",
                        "must_show": [
                            "Lumi kneels on the rug and reaches one arm behind the bed leg",
                            "the ribbon slips farther back when her fingertips brush it",
                            "Lumi uses the handle of her hairbrush to coax the bookmark close enough to pinch",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Magic Quietly Finishes Its Job",
                        "must_show": [
                            "the star blinks two slow times after the bookmark is free",
                            "the star's points fold inward one by one",
                            "Lumi touches the tiny stitched star near the pillow seam",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "Lumi's bed after the lamp clicks off",
                "scene_change": "The bookmark is back in the moon book, and the star rests quietly on the quilt.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Return to Routine",
                        "must_show": [
                            "Lumi slides the silver bookmark between the moon book pages",
                            "the ribbon hangs neatly from the bottom edge of the closed book",
                            "Lumi climbs under the quilt and tucks her feet into the cool corner",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Soft Magical Closing Image",
                        "must_show": [
                            "Mom clicks off the bedside lamp",
                            "the silver ribbon lies still inside the closed moon book",
                            "the stitched star gives one last small glimmer beside Lumi's pillow",
                        ],
                    },
                ],
                "dialogue": [],
                "end_with": "Lumi rests under her quilt while the silver bookmark lies inside the closed moon book and the tiny stitched star glimmers once beside her pillow.",
            },
        ],
    },

    "silly_soft_story": {
        "scene_cards": [
            {
                "scene": 1,
                "paragraphs": [1, 2],
                "setting": "Tessa's bedroom after bath time",
                "scene_change": "Tessa has part of her pajamas on, but the rest of the room is dressed instead.",
                "paragraph_beats": [
                    {
                        "paragraph": 1,
                        "function": "Ordinary Bedtime Setup",
                        "must_show": [
                            "Tessa's towel hangs on the hook after bath time",
                            "Dad lays the folded pajamas on the bed",
                            "Dad names the bedtime order: shirt, pants, slippers, then story",
                        ],
                    },
                    {
                        "paragraph": 2,
                        "function": "Funny Small Problem",
                        "must_show": [
                            "Tessa wears the pajama pants but not the shirt",
                            "the pajama shirt hangs over the bedside lamp like a small tent",
                            "one slipper sits on the windowsill and the other is tucked under the rug",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Tessa",
                        "purpose": "explains the silly reason for the misplaced object",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 2,
                "paragraphs": [3, 4],
                "setting": "beside the lamp in Tessa's bedroom",
                "scene_change": "Dad notices the dressed lamp, and Tessa puts the pajama shirt on herself.",
                "paragraph_beats": [
                    {
                        "paragraph": 3,
                        "function": "Character Notices or Reacts",
                        "must_show": [
                            "Dad looks from the lamp to Tessa and back to the lamp",
                            "the pajama sleeve hangs from the lamp like a floppy ear",
                            "Tessa covers her mouth to hold in a giggle",
                        ],
                    },
                    {
                        "paragraph": 4,
                        "function": "First Funny Fix",
                        "must_show": [
                            "Tessa lifts the pajama shirt off the lamp",
                            "Dad checks the bulb with his hand nearby",
                            "Tessa pulls the shirt over her head and pushes her arms through the sleeves",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Dad",
                        "purpose": "gently names the silly mix-up",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 3,
                "paragraphs": [5, 6],
                "setting": "rug, windowsill, and bed in Tessa's room",
                "scene_change": "The slippers are paired, and the room check turns into one last small joke.",
                "paragraph_beats": [
                    {
                        "paragraph": 5,
                        "function": "Second Funny Fix",
                        "must_show": [
                            "Tessa lifts one slipper down from the windowsill",
                            "Tessa sets it toe-to-toe beside the other slipper on the rug",
                            "Dad pulls the hidden slipper fully out from under the rug",
                        ],
                    },
                    {
                        "paragraph": 6,
                        "function": "Final Check",
                        "must_show": [
                            "Tessa and Dad whisper-check the shirt, lamp, slippers, rug, and pillow",
                            "Tessa picks up her teddy bear and looks at his round ears",
                            "Tessa says Bear is already dressed in fur",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Tessa",
                        "purpose": "adds a small joke during the room check",
                    }
                ],
                "end_with": None,
            },
            {
                "scene": 4,
                "paragraphs": [7, 8],
                "setting": "Tessa's bed after the lamp clicks off",
                "scene_change": "The last joke stays small, and the room settles with every object in place.",
                "paragraph_beats": [
                    {
                        "paragraph": 7,
                        "function": "Last Soft Joke",
                        "must_show": [
                            "Tessa climbs into bed and wiggles her toes under the blanket",
                            "Tessa asks whether her toes need hats too",
                            "Dad tucks the blanket around her feet",
                        ],
                    },
                    {
                        "paragraph": 8,
                        "function": "Calm Bedtime Landing",
                        "must_show": [
                            "Dad sets the storybook on the chair and clicks off the lamp",
                            "the pajama shirt stays on Tessa and the slippers rest together",
                            "Tessa gives one tiny smile into her pillow",
                        ],
                    },
                ],
                "dialogue": [
                    {
                        "speaker": "Tessa",
                        "purpose": "lands the final soft joke",
                    }
                ],
                "end_with": "Tessa smiles into her pillow while her pajama shirt stays on her, the slippers rest together, and the lamp stands bare in the dark room.",
            },
        ],
    },
}

def scene_card_example_for(category_id: str) -> str:
    example = SCENE_CARD_EXAMPLES_BY_CATEGORY.get(
        category_id,
        SCENE_CARD_EXAMPLES_BY_CATEGORY["general_bedtime_story"],
    )
    return json.dumps(example, ensure_ascii=False, indent=2)