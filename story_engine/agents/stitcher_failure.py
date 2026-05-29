from __future__ import annotations

import re
from typing import Any

from story_engine.trace import event as trace_event


SEAM_KIND = {
    "a": "duplicate_adjacent_sentence",
    "b": "high_token_overlap",
    "c": "shared_five_gram",
}
_SEAM_RE = re.compile(r"^seam_([abc])_(\d+)->_\d+:\s*(.*)$")


def parse_seam_issues(issues: list[str]) -> list[dict[str, Any]]:
    seam_failures: list[dict[str, Any]] = []
    for issue in issues:
        match = _SEAM_RE.match(issue)
        if match is None:
            trace_event("pipeline.stitch", unparseable_seam_issue=issue)
            continue
        seam_code, boundary_index, evidence = match.groups()
        seam_failures.append(
            {
                "boundary_index": int(boundary_index),
                "kind": SEAM_KIND[seam_code],
                "evidence": evidence,
            }
        )
    return seam_failures


def build_stitch_failure(seam_check: dict[str, Any], assembled_body: str, blueprint, *, legacy: bool = False) -> dict[str, Any]:
    actual_paragraph_count = len([paragraph for paragraph in assembled_body.split("\n\n") if paragraph.strip()])
    scene_count = blueprint.scene_plan["scene_count"]
    from_scene_plan = scene_count * blueprint.scene_plan["paragraphs_per_scene"]
    if actual_paragraph_count != from_scene_plan:
        trace_event(
            "pipeline.stitch",
            expected_paragraph_count_mismatch=True,
            derived=actual_paragraph_count,
            from_scene_plan=from_scene_plan,
        )

    if legacy and seam_check["ok"]:
        boundary_indexes = list(range(1, scene_count))
        seam_failures = [
            {
                "boundary_index": boundary_index,
                "kind": "legacy_full_boundary_pass",
                "evidence": "",
            }
            for boundary_index in boundary_indexes
        ]
        trace_event(
            "pipeline.stitch",
            event_type="route",
            route="legacy_full_boundary_pass",
            reason="bypass_kill_switch_disabled",
            boundary_indexes=boundary_indexes,
        )
    else:
        seam_failures = parse_seam_issues(seam_check.get("issues", []))

    boundary_indexes = sorted({failure["boundary_index"] for failure in seam_failures})
    return {
        "boundary_indexes": boundary_indexes,
        "seam_failures": seam_failures,
        "expected_paragraph_count": actual_paragraph_count,
    }
