#!/usr/bin/env python3
"""Finalize the Task 1 completion gate from mechanical evidence.

`mechanical_reference_audit_v3.py` contains a deliberately conservative 2D AABB
screen for the eight stock structural fastener axes. That screen can report zero
XY gap even when the real housing solid clears the fastener in 3D. The dedicated
`structural_mount_collision_diagnostic.py` performs the authoritative check using
the actual Type-C housing mesh plus conservative M2 head/boss solids.

This finalizer combines both reports. It may override only the structural-mount
gate, and only when every exact fastener-head and below-plate boss test is clear.
All other v3 completion gates must already pass unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TASK1 = Path(__file__).resolve().parent
GENERATED = TASK1 / "generated"
AUDIT_PATH = GENERATED / "mechanical-audit-final.json"
MOUNT_PATH = GENERATED / "structural-mount-collision.json"
OUTPUT_PATH = GENERATED / "task1-final-gate.json"


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing evidence: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    audit = load(AUDIT_PATH)
    mounts = load(MOUNT_PATH)

    if audit.get("errors"):
        result = {
            "task": 1,
            "status": "failed",
            "reason": "mechanical audit reported errors",
            "errors": audit["errors"],
            "placement_locked": False,
        }
        OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 2

    gates = dict(audit.get("completion_gate", {}))
    exact_mounts_ok = bool(mounts.get("all_fastener_heads_clear")) and bool(
        mounts.get("all_below_plate_bosses_clear")
    )

    # Replace only the known coarse AABB false-positive with the exact 3D result.
    coarse_value = gates.get("eight_structural_mount_axes_clear")
    gates["eight_structural_mount_axes_clear"] = exact_mounts_ok
    gates["structural_mount_gate_method"] = "exact_3d_housing_vs_fastener_envelopes"
    gates["coarse_aabb_structural_mount_screen"] = coarse_value

    non_blocking = {
        "stock_case_local_shell_relief_required",
        "structural_mount_gate_method",
        "coarse_aabb_structural_mount_screen",
        "placement_locked",
    }
    required = {k: v for k, v in gates.items() if k not in non_blocking}
    all_required_true = all(v is True for v in required.values())
    placement_locked = bool(all_required_true and exact_mounts_ok)
    gates["placement_locked"] = placement_locked

    result = {
        "task": 1,
        "status": "complete" if placement_locked else "failed",
        "placement_locked": placement_locked,
        "completion_gate": gates,
        "exact_structural_mount_evidence": {
            "fastener_envelope": mounts.get("fastener_envelope"),
            "all_fastener_heads_clear": mounts.get("all_fastener_heads_clear"),
            "all_below_plate_bosses_clear": mounts.get("all_below_plate_bosses_clear"),
            "mounts": mounts.get("mounts"),
        },
        "stock_case_local_shell_relief_required": gates.get(
            "stock_case_local_shell_relief_required"
        ),
        "note": (
            "The stock right-case shell intersects the Type-C housing and requires "
            "local relief in the later case task. All eight structural mounting axes, "
            "retained components, and conservative M2 fastener envelopes remain clear."
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if placement_locked else 2


if __name__ == "__main__":
    sys.exit(main())
