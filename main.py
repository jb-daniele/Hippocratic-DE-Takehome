import argparse
import json

from story_engine import persistence, trace
from story_engine.errors import RunFailed
from story_engine.pipeline import revise_with_feedback, run
from story_engine.schemas import RequestOptions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a StoryNest bedtime story draft.")
    parser.add_argument("--request", help="Story request. If omitted, you will be prompted.")
    parser.add_argument(
        "--mode",
        choices=[
            "auto_detect",
            "classic",
            "animal",
            "gentle_adventure",
            "magical",
            "friendship",
            "silly",
            "educational",
        ],
        default="auto_detect",
    )
    parser.add_argument("--character", default="")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--feedback", action="store_true")
    return parser.parse_args()


def _trace_events(trace_id: str | None) -> list[dict]:
    if not trace_id:
        return []
    path = trace.trace_path(trace_id)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def print_debug(package, trace_id: str | None = None) -> None:
    print("Debug")
    if trace_id:
        print(f"Trace path: {trace.trace_path(trace_id)}")
    classify_events = [event for event in _trace_events(trace_id) if event.get("stage") == "agent.classify"]
    if classify_events:
        classifier = classify_events[-1]
        print(
            "Classifier: "
            f"category_id={classifier.get('category_id')}, "
            f"display={classifier.get('category_display_name')}, "
            f"confidence={classifier.get('classifier_confidence')}, "
            f"fallback={classifier.get('fallback')}, "
            f"skipped={classifier.get('classifier_skipped')}, "
            f"examples={classifier.get('few_shot_examples_retrieved')}"
        )
    print("Stages:")
    for event in _trace_events(trace_id):
        stage = event.get("stage")
        latency = event.get("latency_ms")
        bits = []
        for key in ("category_id", "approved", "allowed", "fallback", "classifier_skipped", "actual_word_count"):
            if key in event:
                bits.append(f"{key}={event[key]}")
        if latency is not None:
            bits.append(f"latency_ms={latency}")
        print(f"- {stage}" + (f" ({', '.join(bits)})" if bits else ""))
    for iteration, reports in enumerate(package.judge_trail, start=1):
        print(f"Judge iteration {iteration}")
        for report in reports:
            print(f"- {report['judge_name']}: {report['verdict']}")
            print(f"  reason: {report['reason']}")
            print(f"  revision_guidance: {report['revision_guidance']}")
    print(f"Approved: {package.approved}")
    print(f"Iterations used: {package.iterations_used}")
    if package.warnings:
        print("Warnings:")
        for warning in package.warnings:
            print(f"- {warning}")
    print()


def print_cover(package, *, debug: bool = False, trace_id: str | None = None) -> None:
    cover = package.cover
    print("Cover")
    print(f"Title: {cover['title']}")
    print(f"Category: {cover['category_chip']}")
    print(f"Words: {cover['actual_word_count']}")
    if cover["characters"]:
        print(f"Characters: {', '.join(cover['characters'])}")
    print(f"Pages: {len(package.pages)}")
    print()

    if debug:
        print_debug(package, trace_id=trace_id)


def walk_pages(package) -> None:
    for index, page in enumerate(package.pages, start=1):
        print(f"Page {index} of {len(package.pages)}")
        print(page)
        print()
        if index < len(package.pages):
            try:
                input("Press Enter for the next page...")
            except EOFError:
                return


def print_package(package, *, debug: bool = False, trace_id: str | None = None) -> None:
    print_cover(package, debug=debug, trace_id=trace_id)
    walk_pages(package)


def main() -> None:
    args = parse_args()
    request = args.request or input("What kind of story do you want to hear? ")
    options = RequestOptions(
        story_mode=args.mode,
        main_character_name=args.character,
    )
    trace_id = persistence.run_id_for("cli-generation")
    try:
        with trace.Run(trace_id):
            package = run(request, options)
    except RunFailed as exc:
        print(f"Run failed: {exc.failure_category}")
        raise
    print_package(package, debug=args.debug, trace_id=trace_id)
    if args.feedback:
        feedback = input("Changes? Press Enter to keep the story: ").strip()
        if feedback:
            with trace.Run(trace_id):
                package = revise_with_feedback(package, feedback, request)
            print_package(package, debug=args.debug, trace_id=trace_id)


if __name__ == "__main__":
    main()
