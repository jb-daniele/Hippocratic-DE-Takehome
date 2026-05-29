from __future__ import annotations

from typing import Any

from story_engine.categories import CATEGORIES
from story_engine.config import STORIES_DIR
from story_engine.persistence import store


SEED_CREATED_AT = "2026-05-28T00:00:00Z"

_CATEGORY_DISPLAY_NAMES = {category["id"]: category["display_name"] for category in CATEGORIES}


SEED_EXAMPLES: list[dict[str, Any]] = [
    {
        "slug": "sunnys-first-game",
        "title": "Sunny's First Game",
        "category_id": "friendship_and_feelings",
        "characters": ["Sunny Mole", "Lily Rabbit", "Finch", "Squirrel"],
        "main_characters": ["Sunny Mole"],
        "ending_image": "Sunny rests with Lily and the meadow friends around his pebble in the golden light.",
        "gentle_conflict": "Sunny wants to join the game but feels nervous about getting in the way.",
        "source_request": "Write a gentle friendship story about a shy mole joining a meadow game.",
        "body": """Sunny Mole sat at the edge of the clover patch while the meadow animals played ring-tag in the late afternoon light. Lily Rabbit hopped around the circle, Finch fluttered from stump to stone, and Squirrel darted between the tall grass stems. Every time someone was tagged, they laughed and traded places, and the game spun round and round like a wheel. Sunny held a smooth gray pebble in both paws and watched, turning it over and over while the others ran.

Sunny wanted to play, but his paws stayed tucked under him. When Lily ran close, he opened his mouth to call out, then shut it again before any words came. He shuffled behind a tall dandelion stalk and rubbed one paw over the pebble until it grew warm. "They already know how to play," he whispered to himself. "I'll only get in the way."

Sunny took two small steps toward the circle, his nose twitching. Just then Finch swooped past, laughing, "Tag Squirrel next!" and Squirrel zipped behind a buttercup so fast the petals shook. Sunny stopped so suddenly that his nose bumped the clover leaves. He backed up to the dandelion and looked down at his pebble again.

Lily slowed when she saw Sunny standing by himself. She hopped out of the game and came to his side, leaving little prints in the soft dirt. "Do you want a first turn that's easy?" she asked. Then she held out one paw and stood very still. "You can tag me before I run. I won't move until you do."

Sunny looked at Lily's paw, then at the circle of animals waiting beyond her. He reached out slowly and gave her paw one careful tap. "Tag," he said, very quietly. Lily sprang away with a happy laugh and called over her shoulder, "Sunny tagged me! Now I chase Finch!"

Finch landed on the low stump and waved one wing. "Let's make the circle wider," he said. Squirrel pushed two fallen leaves out of the way to clear a path, and the rabbits hopped back so Sunny had plenty of room. Then Lily ran past Sunny again — slowly this time, close enough for him to reach but far enough to make it a real game.

Sunny's paws began to move faster over the grass. He laughed out loud when Squirrel peeked from behind a daisy with only his bushy tail showing. When Finch fluttered down low, Sunny reached out and tapped the stump instead of Finch's wing, and Finch said, "That counts for a mole turn." Sunny grinned so wide that his pebble slipped right out of his paws and bounced softly into the clover.

When the game ended, the animals flopped down together in the cool grass. Lily settled beside Sunny near the dandelion, and Finch tucked his head under one wing on the stump while Squirrel curled his tail around his feet. Sunny's pebble rested in the middle of the clover circle, gray and smooth, where everyone could see it. The meadow grew quiet around them, and Sunny leaned his shoulder gently against Lily's side as the last of the sunlight went gold.""",
    },
    {
        "slug": "nora-and-the-steam-cloud",
        "title": "Nora and the Steam Cloud",
        "category_id": "general_bedtime_story",
        "characters": ["Nora", "Dad"],
        "main_characters": ["Nora"],
        "ending_image": "Nora leans against Dad in the warm kitchen after wiping the little moon from the window.",
        "gentle_conflict": "Nora wonders where steam goes after it disappears.",
        "source_request": "Write a calm bedtime story about a child noticing steam in the kitchen.",
        "body": """Nora sat at the kitchen table while Dad poured warm tea into his blue mug. A pale ribbon of steam rose from the top and curled slowly above the cup. Nora leaned forward with both elbows on the table, watching the steam wiggle, thin out, and fade into nothing. Up in the corner of the window over the sink, one small patch of glass had gone cloudy and gray.

Nora pointed at the mug. "Where does the steam go when I can't see it anymore?" she asked. Dad set the kettle safely on the back of the counter, away from the edge. Then he pulled his chair closer and looked at the little white curls drifting up from the tea. "That's a good kitchen question," he said.

"The tea is warm," Dad said, "so tiny bits of water float up off the top as steam." Nora watched the wispy curls lift and disappear. Dad held his hands apart, as if cupping something rising between them. "And when those tiny bits get cool again, they can turn back into little drops of water."

Dad opened the drawer and took out a clean metal spoon. He pressed the bowl of it against the cool window for a moment to chill it, then held it up by the handle. "We can look without touching the hot mug," he said. He held the cold spoon just above the steam, high enough that Nora could see right into the shiny bowl.

The steam brushed against the spoon and vanished where it touched. Nora waited, holding very still so she wouldn't miss anything. Tiny drops began to gather on the cold underside — first like little pinpricks, then growing into clear, round beads. One bead grew heavy, slid down the curve of the spoon, and stopped at the very edge.

"Look! The steam touched the cold spoon and turned back into water!" Nora said, pointing with one finger. Dad nodded and lowered the spoon gently onto a folded napkin. Nora bent close to study the row of beads without touching them. In the kitchen light they shone like small round buttons.

Then Nora looked over at the cloudy patch on the kitchen window. She leaned in and breathed softly on the glass, and a foggy little circle bloomed where her warm breath landed. With one fingertip she drew a tiny moon inside it. "More little drops," she said, "from me this time." Dad smiled and ran the spoon under the tap.

When the tea was gone, Dad carried the empty mug to the sink. Nora wiped her little moon from the window with the corner of a dish towel until the glass was clear again. The kettle sat quiet on the stove, and the spoon rested dry beside the folded napkin. Nora leaned against Dad's arm while the kitchen light glowed warm on the clean table.""",
    },
    {
        "slug": "milos-leaf-roof",
        "title": "Milo’s Leaf Roof",
        "category_id": "cozy_animal_story",
        "characters": ["Milo Mouse", "Junie Snail"],
        "main_characters": ["Milo Mouse"],
        "ending_image": "Milo rests dry under the patched leaf roof while Junie listens to the rain.",
        "gentle_conflict": "Milo needs to mend a small gap in his burrow roof before rain drips through.",
        "source_request": "Write a cozy animal story about a mouse fixing his leaf roof before bedtime.",
        "body": """Milo Mouse lived in a little burrow beneath the blackberry hedge, where the tangled roots made a round brown ceiling over his bed. Each evening he swept the doorway with a fern stem and lined his sleeping nook with dry oak leaves. His thimble cup sat on a flat gray stone, and his red thread blanket lay folded neatly at the foot of the nest. Before climbing in, Milo always reached up and tapped the leaf roof once with his paw to make sure it was snug.

That night, when Milo tapped the roof, one dry leaf slipped loose and drifted straight down onto his nose. He looked up and saw a small open patch of sky between two roots. "Rain could drip right through there," he said, turning the fallen leaf over in both paws. A cool breeze slid in through the gap and made the corner of his blanket flutter.

Milo climbed up onto the flat stone and tried to press the leaf back into the hole. He stretched as tall as he could on his back paws, but the leaf only bent in the middle and floated down again. He tried a wider leaf next, pushing it up with the fern stem. The leaf turned sideways, sailed past him, and landed smack on top of the thimble cup like a little green hat.

A soft rustle came from the doorway, and Junie Snail slid in with a curled strip of birch bark balanced on her shell. "Your roof has a little mouth in it," Junie said, peering up at the gap. She reached out and touched the loose leaves with one feeler. "A flat patch like that needs something stiff behind it, or the leaves just keep falling."

Milo fetched three dry oak leaves from his leaf basket while Junie nudged the strip of birch bark up between the roots. Milo held the bark steady with the fern stem, and Junie pressed the first leaf flat against it until it stuck. Then Milo tucked the bottom edge of a second leaf under the first, the way shingles overlap on the garden shed. Junie smoothed the last leaf into the corner with the side of her shell.

The open patch disappeared. Milo climbed back onto the flat stone and tapped the mended roof once, then twice — and every leaf stayed exactly where it was. To be sure, Junie gave the doorway vine a gentle shake, and a few cool drops from outside rolled down the hedge. Milo watched closely, but not a single drop came through the roof.

Milo lifted the leaf hat off his thimble cup and set the cup neatly back on its stone. Then he tucked the red thread blanket around his paws and looked up at the patched ceiling. "It sounds quieter up there now," he said. Junie settled herself by the doorway on a damp pebble and folded her feelers halfway in.

Outside, rain began to patter softly on the blackberry leaves. Inside, the birch bark held the oak leaves firm and dry between the roots. Milo's blanket stayed warm, and his thimble cup gleamed on its little stone. Junie listened to the rain from the doorway while the burrow grew quiet and still.""",
    },
    {
        "slug": "lena-gets-bear-ready",
        "title": "Lena Gets Bear Ready",
        "category_id": "general_bedtime_story",
        "characters": ["Lena", "Bear", "Mom"],
        "main_characters": ["Lena"],
        "ending_image": "Lena holds Bear in the quiet room while a thin line of hallway light glows under the door.",
        "gentle_conflict": "Lena needs to get Bear out of his daytime sweater and ready for sleep.",
        "source_request": "Write a gentle bedtime story about a child helping a teddy bear get ready for bed.",
        "body": """Lena had brushed her teeth, rinsed her cup, and picked the moon book down from the low shelf. Her room smelled faintly of clean pajamas and lavender soap. The curtain was open just a finger-width, showing one narrow square of dark blue sky. Bear sat propped against the pillow, waiting with his round ears tilted to one side.

Lena reached for Bear and then stopped. He was still wearing his yellow daytime sweater, the one with the tiny apple stitched on the front. "Bear can't sleep in his outside sweater," Lena said, holding him up under the arms. There was a small jam spot, dried hard now, on his chin from afternoon toast.

Lena carried Bear to the little table beside her bed. She dipped one corner of a washcloth into her water cup and wiped the jam spot in slow, careful circles until it faded away. But the sweater still stayed bunched around Bear's soft middle. She tugged at one sleeve, then frowned when Bear's whole paw vanished up inside it.

Mom came to the doorway with the laundry basket on her hip. "Let's find his sleep sack," she said, setting the basket down with a soft thump. She opened the bottom drawer and rummaged through it while Lena held Bear steady. Together they slipped the sweater up over Bear's ears, and Mom folded it into a neat yellow square.

The sleep sack was blue with one white button on the front. Lena guided Bear's feet down inside it and pulled it up to his chin. Mom fastened the button while Lena gently smoothed Bear's ears flat against his head. Then they tucked the moon book in beside him, turned so he could see the silver picture on the cover.

Lena made her bedtime check around the room, pointing as she went. "Water cup on the shelf. Socks in the basket. Book on the blanket. Curtain open a little." She nudged one stray slipper under the chair so nobody would trip on it in the morning. Mom pushed the closet door until it clicked snug in its frame.

Lena climbed into bed and tucked Bear against her shoulder. She pulled the blanket up over Bear's paws first, then over her own knees. Mom sat on the edge of the bed and read the first two pages of the moon book in a low, even voice. Lena turned the last page slowly, so Bear wouldn't miss the picture of the little sleeping house.

Mom set the book on the table and kissed the top of Lena's hair. The hallway light clicked off, leaving a thin golden line glowing under the door. Bear's clean chin rested just above the blue sleep sack, and Lena's hand stayed curled around his paw. Outside the narrow gap in the curtain, the small square of sky held perfectly still.""",
    },
    {
        "slug": "suri-returns-the-basket",
        "title": "Suri Returns the Basket",
        "category_id": "gentle_adventure",
        "characters": ["Suri", "Mrs. Vale", "Dad"],
        "main_characters": ["Suri"],
        "ending_image": "Suri washes her hands inside while the blue gate rests still in the quiet garden.",
        "gentle_conflict": "Suri carries a borrowed basket back across the garden before pajama time.",
        "source_request": "Write a gentle adventure about a child returning a basket across a safe garden path.",
        "body": """Suri found Mrs. Vale's small willow basket on the kitchen bench after supper. It had carried warm rolls to their house that morning, and now it sat empty except for one clean cloth folded neatly inside. "I can bring it back before pajama time," Suri said, lifting it by the handle. Dad looked out at the quiet garden path, where the evening had turned soft and gold, and nodded.

Dad stood on the porch and pointed the way for her. "Past the bean rows, around the little shed, through the blue gate, and straight to Mrs. Vale's back step," he said. Suri repeated it back while she held the basket handle with both hands. "Bean rows, shed, blue gate, back step." Dad stayed right there on the porch, where she could turn around and see him the whole time.

Suri walked between the bean rows, counting the flat stepping stones under her shoes. One, two, three, four, five. A snail was making its slow way across the next stone, so she stepped carefully around it and shifted the basket onto her hip. The bean leaves brushed her sleeve as she passed, and behind her the kitchen window glowed warm and square in the dusk.

Near the shed, the basket handle snagged on a low plum branch. Instead of yanking it, Suri stopped and thought for a moment. She held the handle steady with one hand and bent the springy branch down with the other until the basket slipped free. A small leaf had dropped into the basket, so she fished it out and set it gently beside the path.

The blue gate stood open just wide enough for her to slip through. Mrs. Vale was out on her back step, shaking crumbs from a tea towel into the flower bed. Suri held out the willow basket with both hands. "Thank you for the rolls," she said, and Mrs. Vale smiled, tucked the folded cloth back inside, and took the basket from her.

On the way home, the garden looked a little different from this side, as if it had quietly turned around. The shed came first now, then the bean rows, then the porch light glowing beyond them. Suri trailed her fingers along each fence post as she passed back through the blue gate. When she reached the plum branch, she remembered to duck her head before the handle could catch.

Dad lifted one hand from the porch rail the moment Suri came back into view. "Bean rows, shed, blue gate, back home," she called softly, retracing the path out loud. The kitchen door stood open behind him, and the yellow light spilled in a bright stripe across the porch boards. Suri climbed the steps and brushed one bit of garden dirt from her shoe.

Inside, Dad pulled the door shut, and the last green smell of bean leaves drifted in with her. The empty spot on the kitchen bench looked tidy and settled now. Suri washed her hands at the sink while Dad laid her pajamas over the chair by the warm stove. Outside, the blue gate rested still in the dim and quiet garden.""",
    },
    {
        "slug": "lumi-and-the-star-on-the-quilt",
        "title": "Lumi and the Star on the Quilt",
        "category_id": "magical_bedtime_story",
        "characters": ["Lumi", "Mom"],
        "main_characters": ["Lumi"],
        "ending_image": "A tiny stitched star gives one last soft glimmer beside Lumi's pillow.",
        "gentle_conflict": "Lumi cannot find the silver ribbon bookmark for her moon book.",
        "source_request": "Write a magical bedtime story about a glowing star helping a child find a bookmark.",
        "body": """Lumi was getting ready for bed in her room at the end of the hall. She had stacked her picture books beside the lamp and folded her socks into the small basket by the chair. Her blue quilt was turned down, and her pajamas were buttoned all the way to the top. Only one thing was missing: the silver ribbon bookmark for her moon book.

Lumi riffled through the pages of the book, but the bookmark wasn't tucked inside any of them. Then, right at the edge of her pillow, a tiny glow blinked on. It was shaped like a star and no bigger than a coat button. The little glow winked once, then stretched a thin line of light straight across the quilt.

Lumi lifted the pillow up with both hands. Underneath sat a small star of light, flat and bright, as if someone had snipped it out of moonshine. It didn't fly, or buzz, or make a single sound. But when Lumi leaned in close to look, the star slowly tipped one of its points toward the side of the bed.

That point cast a faint silver stripe across the floorboards. Lumi followed the stripe with her eyes until it reached the shadow behind the bed leg. There, tucked just under the wooden rail, a curl of silver ribbon lay against the wall. "You found my bookmark," Lumi whispered to the star.

The star could point, but it couldn't reach — so Lumi knelt down on the rug and slid one arm carefully behind the bed leg. Her fingertips brushed the ribbon, but it only slipped farther back into the shadow. She fetched her hairbrush and used the handle to coax the bookmark closer, then pinched it between two fingers. A little dust bunny came along with it, so she brushed the ribbon clean against her pajama knee.

The star on the quilt blinked two slow times, as if it were satisfied. Its bright points folded gently inward, one by one, until it had become a tiny stitched star sewn near the pillow seam. Lumi reached out and touched the stitch with one finger. It felt like ordinary thread now, just a little warm from the lamp.

Lumi slid the silver bookmark back between the pages of her moon book where it belonged. She set the book on the bedside table with the ribbon hanging neatly from the bottom edge. Then she climbed under the quilt and tucked her feet down into the smooth, cool corner. The lamp made one small circle of light beside her hand.

Mom opened the door just wide enough to say good night, then reached in and clicked the lamp off. The silver ribbon lay still inside the closed book. On the quilt, the tiny stitched star rested quietly beside Lumi's pillow. In the dark room it gave one last soft glimmer, then settled into a still, quiet dot.""",
    },
    {
        "slug": "tessa-dresses-the-room",
        "title": "Tessa Dresses the Room",
        "category_id": "silly_soft_story",
        "characters": ["Tessa", "Dad", "Bear"],
        "main_characters": ["Tessa"],
        "ending_image": "Tessa smiles in bed while the room stands bare and proper in the dark.",
        "gentle_conflict": "Tessa dresses the room instead of finishing her own pajamas.",
        "source_request": "Write a silly soft bedtime story about a child putting pajamas on the room.",
        "body": """Tessa was supposed to put on her pajamas after bath time. Her towel hung on the hook, her hair was combed flat and damp, and her toothbrush cup sat upside down by the sink to dry. Dad laid the folded pajamas on the bed and patted the stack. "Shirt, pants, slippers, then story," he said.

When Dad came back with the storybook, Tessa was wearing the pajama pants — but not the shirt. The shirt was draped over the bedside lamp like a small sleepy tent. One slipper perched up on the windowsill, and the other was tucked halfway under the edge of the rug. Tessa pointed at the lamp and said, "It looked chilly."

Dad looked at the lamp, then back at Tessa, then at the lamp again. "Did you dress the room instead of yourself?" he asked. Tessa pressed both hands over her mouth to keep her giggle from getting out. The lamp leaned a little under the shirt, with one empty sleeve hanging down like a long, floppy ear.

Tessa lifted the pajama shirt off the lamp. Dad held his hand near the bulb to check it and said, "Lamps don't need pajamas — especially warm, cozy ones." Tessa pulled the shirt over her own head, hunted for the neck hole, and finally pushed both arms through the right sleeves. Dad tugged the hem down so the little buttons lined up straight.

Next, Tessa rescued the slipper from the windowsill. "This one wanted the best view of the garden," she said, holding it up. She marched it over and set it beside its partner, toe to toe on the rug. Dad fished the hidden slipper out from under the rug and tapped the pair into a tidy line beside the bed.

Then they checked the whole room together in a soft, whispery list. "Shirt on Tessa. Lamp plain. Slippers paired. Rug flat. Pillow not wearing anything." Tessa picked up her teddy bear and peered closely at his round ears. "Bear's already dressed — in fur," she said, and Dad nodded slowly, as if this were very important news.

Tessa climbed into bed and wiggled her toes under the blanket. "Do my toes need hats too?" she asked, peeking up at him. Dad tucked the blanket snugly around her feet and said, "Only blanket hats tonight." Tessa gave one tiny snort-laugh into her pillow.

Dad set the storybook on the chair and clicked off the lamp. The pajama shirt stayed on Tessa, the slippers rested together by the rug, and the lamp stood bare and proper on the table at last. Tessa smiled once into her pillow. The room held perfectly still, wearing only the dark.""",
    },
]


def _word_count(text: str) -> int:
    return len(text.split())


def _pages_for(body: str) -> list[str]:
    pages: list[str] = []
    current: list[str] = []
    current_words = 0
    for paragraph in body.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph_words = _word_count(paragraph)
        if current and current_words + paragraph_words > 140:
            pages.append("\n\n".join(current))
            current = []
            current_words = 0
        current.append(paragraph)
        current_words += paragraph_words
    if current:
        pages.append("\n\n".join(current))
    return pages


def _build_seed_payload(index: int, seed: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    run_id = f"example-{index:03d}-{seed['slug']}"
    category_id = seed["category_id"]
    display_name = _CATEGORY_DISPLAY_NAMES[category_id]
    body = seed["body"]
    pages = _pages_for(body)
    actual_word_count = _word_count(body)
    cover = {
        "title": seed["title"],
        "category_display_name": display_name,
        "category_chip": display_name,
        "characters": [],
        "category_id": category_id,
        "actual_word_count": actual_word_count,
        "page_count": len(pages),
        "fallback": False,
        "classifier_skipped": True,
    }
    index_entry = {
        "run_id": run_id,
        "id": run_id,
        "created_at": SEED_CREATED_AT,
        "title": seed["title"],
        "cover": cover,
        "story_mode": "auto_detect",
        "category_id": category_id,
        "category_display_name": display_name,
        "classifier_confidence": "high",
        "classifier_rationale": "Seeded example.",
        "classifier_matched_signals": [],
        "classifier_fallback_status": False,
        "classifier_skipped": True,
        "actual_word_count": actual_word_count,
        "characters": seed["characters"],
        "pages": pages,
        "page_break_suggestions": [],
        "gentle_conflict": seed["gentle_conflict"],
        "ending_closure_plan": seed["ending_image"],
        "body": body,
        "source_request": seed["source_request"],
        "user_rating": 5,
        "rating_recorded_at": SEED_CREATED_AT,
        "story_json_path": f"stories/{run_id}/story.json",
        "story_html_path": f"stories/{run_id}/story.html",
        "is_example": True,
    }
    blueprint = {
        "title": seed["title"],
        "category_id": category_id,
        "category_display_name": display_name,
        "main_characters": seed["main_characters"],
        "story_spine": {
            "central_problem": seed["gentle_conflict"],
            "ending_image": seed["ending_image"],
        },
        "character_cards": [],
        "scene_cards": [],
        "selected_story_mode": "auto_detect",
    }
    request_options = {
        "story_mode": "auto_detect",
        "main_character_name": seed["main_characters"][0] if seed["main_characters"] else "",
    }
    classification = {
        "category_id": category_id,
        "category_display_name": display_name,
        "classifier_confidence": "high",
        "classifier_rationale": "Seeded.",
        "matched_signals": [],
        "fallback": False,
        "classifier_skipped": True,
        "selected_story_mode": "auto_detect",
        "request_text": seed["source_request"],
        "main_characters": seed["main_characters"],
    }
    final_package = {
        "story": {"title": seed["title"], "body": body},
        "blueprint": blueprint,
        "cover": cover,
        "pages": pages,
        "page_break_suggestions": [],
        "actual_word_count": actual_word_count,
        "request": request_options,
    }
    payload = {
        "run_id": run_id,
        "created_at": SEED_CREATED_AT,
        "request_options": request_options,
        "classification": classification,
        "blueprint": blueprint,
        "final_package": final_package,
        "index_entry": index_entry,
    }
    return run_id, payload


def ensure_seed_examples() -> None:
    entries = store._read_index_entries()
    seed_payloads = [_build_seed_payload(index, seed) for index, seed in enumerate(SEED_EXAMPLES, start=1)]
    seed_run_ids = {run_id for run_id, _ in seed_payloads}
    entries = [entry for entry in entries if entry.get("run_id") not in seed_run_ids]

    for run_id, payload in seed_payloads:
        run_dir = STORIES_DIR / run_id
        store.ensure_dir(run_dir)
        entry = payload["index_entry"]
        store._write_json(run_dir / "story.json", payload)
        (run_dir / "story.html").write_text(store._render_story_html(entry), encoding="utf-8")
        entries.append(entry)

    store._write_index_entries(entries)
    store.render_index_html()
