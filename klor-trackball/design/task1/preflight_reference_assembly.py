#!/usr/bin/env python3
"""Task 1 mechanical-reference-assembly preflight.

This tool deliberately does not edit any production CAD/PCB source. It verifies
that the required stock sources exist, verifies the exact external Type-C STEP
when supplied, and can export a stock board-only STEP using KiCad CLI.

It does not declare the placement locked. Cross-model transforms and collision
checks remain Task 1 work and are tracked in reference_assembly_manifest.yaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_HOUSING_SHA256 = (
    "79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c"
)

TASK1_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TASK1_DIR.parents[1]

SOURCES = {
    "pcb": PROJECT_DIR / "klor1.4/PCB/klor1_4/klor1_4.kicad_pcb",
    "switchplate": PROJECT_DIR
    / "klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.step",
    "case_right": PROJECT_DIR
    / "klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl",
    "breakout": PROJECT_DIR
    / "klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_pcb_step(pcb: Path, output: Path) -> dict[str, object]:
    cli = shutil.which("kicad-cli")
    if not cli:
        return {
            "ok": False,
            "reason": "kicad-cli not found",
            "output": str(output),
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        cli,
        "pcb",
        "export",
        "step",
        "--board-only",
        "--force",
        "--output",
        str(output),
        str(pcb),
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    return {
        "ok": proc.returncode == 0 and output.exists(),
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "output": str(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--housing-step",
        type=Path,
        help="Path to the exact Keyball 25 mm Type-C STEP from Thingiverse 6719828.",
    )
    parser.add_argument(
        "--export-pcb-step",
        action="store_true",
        help="Export a stock board-only STEP into design/task1/generated/.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for the machine-readable preflight report.",
    )
    args = parser.parse_args()

    report: dict[str, object] = {
        "task": 1,
        "placement_locked": False,
        "sources": {},
        "housing": {
            "provided": bool(args.housing_step),
            "expected_sha256": EXPECTED_HOUSING_SHA256,
        },
    }

    sources_ok = True
    for name, path in SOURCES.items():
        exists = path.exists()
        sources_ok &= exists
        report["sources"][name] = {
            "path": str(path),
            "exists": exists,
        }

    housing_ok = False
    if args.housing_step:
        housing_path = args.housing_step.expanduser().resolve()
        if housing_path.exists():
            actual_hash = sha256(housing_path)
            housing_ok = actual_hash == EXPECTED_HOUSING_SHA256
            report["housing"].update(
                {
                    "path": str(housing_path),
                    "exists": True,
                    "actual_sha256": actual_hash,
                    "hash_matches": housing_ok,
                }
            )
        else:
            report["housing"].update(
                {"path": str(housing_path), "exists": False, "hash_matches": False}
            )

    if args.export_pcb_step and SOURCES["pcb"].exists():
        report["pcb_step_export"] = export_pcb_step(
            SOURCES["pcb"], TASK1_DIR / "generated/klor1_4.step"
        )

    report["preflight_passed"] = sources_ok and housing_ok
    report["remaining_task1_work"] = [
        "derive and record PCB-to-switchplate transform",
        "derive and record PCB-to-case transform",
        "place Type-C STEP in Z using the real switchplate interface",
        "place real Kivipallur breakout geometry and verify service path",
        "add verified R32/R33, encoder, MCU and TRRS envelopes",
        "run complete collision/access audit",
        "update completion gate and lock placement only if every check passes",
    ]

    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    # Missing external housing is an expected Task 1 blocker, so return non-zero
    # whenever the preflight cannot yet support a source-geometry assembly.
    return 0 if report["preflight_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
