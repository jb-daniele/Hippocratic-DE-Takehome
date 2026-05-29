from pathlib import Path


MODEL = "gpt-3.5-turbo"
AGENT_TEMPERATURES = {
    "classifier": 0.0,
    "character_designer": 0.3,
    "arc_planner": 0.2,
    "scene_planner": 0.2,
    "scene_writer": 0.4,
    "scene_rewriter": 0.4,
    "scene_stitcher": 0.0,
    "title_writer": 0.5,
    "safety_judge": 0.0,
    "coherence_judge": 0.0,
    "language_judge": 0.1,
    "polish": 0.2,
}
SCENE_PLAN = {"scene_count": 4, "paragraphs_per_scene": 2}
SCENE_STITCHER_BYPASS_ENABLED = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = PROJECT_ROOT / "stories"
LOGS_DIR = PROJECT_ROOT / "logs"
PROMPT_EXAMPLE_CANDIDATES_DIR = PROJECT_ROOT / "data" / "prompt_example_candidates"


def scene_plan_for(category_id: str) -> dict[str, int]:
    return SCENE_PLAN.copy()
