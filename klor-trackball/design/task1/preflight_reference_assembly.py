#!/usr/bin/env python3
"""Task 1 mechanical-reference-assembly preflight.

This tool deliberately does not edit production CAD/PCB source. It verifies the
required stock sources and the checked-in Type-C housing models, and can export
an unmodified stock PCB as a board-only STEP using KiCad CLI.

The unarchived housing STEP/STLs are the primary Task 1 sources. The original ZIP
is retained only as an optional provenance cross-check.

This script never declares placement locked. Cross-model transforms and collision
checks remain Task 1 work and are tracked in reference_assembly_manifest.yaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

EXPECTED_ARCHIVE_SHA256 = (
    "ad2ee79388c01fcb775ee08e35761d14b27fbd53ecffabfbdc45add77830e206"
)
EXPECTED_STEP_SHA256 = (
    "79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c"
)
EXPECTED_LEFT_STL_SHA256 = (
    "5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58"
)
EXPECTED_RIGHT_STL_SHA256 = (
    "9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565"
)
EXPECTED_STEP_MEMBER = "files/keyball_trackball_case_25mm_type_c.stp"

TASK1_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TASK1_DIR.parents[1]
HOUSING_DIR = PROJECT_DIR / "Keyball 25mm Trackball Case Type C - 6719828"
DEFAULT_HOUSING_STEP = HOUSING_DIR / "files/keyball_trackball_case_25mm_type_c.stp"
DEFAULT_LEFT_STL = HOUSING_DIR / "files/keyball_trackball_case_25mm_type_c_left.stl"
DEFAULT_RIGHT_STL = HOUSING_DIR / "files/keyball_trackball_case_25mm_type_c_right.stl"
DEFAULT_HOUSING_ARCHIVE = PROJECT_DIR / "Keyball 25mm Trackball Case Type C - 6719828.zip"

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


def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected_sha256: str) -> dict[str, object]:
    result: dict[str, object] = {
        "path": str(path),
        "exists": path.exists(),
        "expected_sha256": expected_sha256,
        "ok": False,
    }
    if not path.exists():
        return result

    actual_hash = sha256(path)
    result["actual_sha256"] = actual_hash
    result["hash_matches"] = actual_hash == expected_sha256
    result["ok"] = result["hash_matches"]
    return result


def verify_direct_housing_sources(
    step: Path, left_stl: Path, right_stl: Path
) -> dict[str, object]:
    models = {
        "step": verify_file(step, EXPECTED_STEP_SHA256),
        "left_stl": verify_file(left_stl, EXPECTED_LEFT_STL_SHA256),
        "right_stl": verify_file(right_stl, EXPECTED_RIGHT_STL_SHA256),
    }
    return {
        "models": models,
        "ok": all(bool(model["ok"]) for model in models.values()),
    }


def verify_housing_archive(archive: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": str(archive),
        "exists": archive.exists(),
        "expected_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "expected_step_member": EXPECTED_STEP_MEMBER,
        "expected_step_sha256": EXPECTED_STEP_SHA256,
        "ok": False,
    }
    if not archive.exists():
        return result

    archive_hash = sha256(archive)
    result["actual_archive_sha256"] = archive_hash
    result["archive_hash_matches"] = archive_hash == EXPECTED_ARCHIVE_SHA256

    try:
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            result["zip_readable"] = True
            result["step_member_present"] = EXPECTED_STEP_MEMBER in names
            if EXPECTED_STEP_MEMBER in names:
                with zf.open(EXPECTED_STEP_MEMBER) as step_fh:
                    step_hash = sha256_stream(step_fh)
                result["actual_step_sha256"] = step_hash
                result["step_hash_matches"] = step_hash == EXPECTED_STEP_SHA256
            else:
                result["step_hash_matches"] = False
    except (OSError, zipfile.BadZipFile) as exc:
        result["zip_readable"] = False
        result["error"] = str(exc)
        result["step_member_present"] = False
        result["step_hash_matches"] = False

    result["ok"] = bool(
        result.get("archive_hash_matches")
        and result.get("zip_readable")
        and result.get("step_member_present")
        and result.get("step_hash_matches")
    )
    return result


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
        default=DEFAULT_HOUSING_STEP,
        help="Checked-in Type-C STEP. Defaults to the unarchived repository file.",
    )
    parser.add_argument(
        "--housing-left-stl",
        type=Path,
        default=DEFAULT_LEFT_STL,
        help="Checked-in left STL used for source-package verification.",
    )
    parser.add_argument(
        "--housing-right-stl",
        type=Path,
        default=DEFAULT_RIGHT_STL,
        help="Checked-in right STL used for source-package verification.",
    )
    parser.add_argument(
        "--housing-archive",
        type=Path,
        default=DEFAULT_HOUSING_ARCHIVE,
        help="Optional original ZIP provenance cross-check.",
    )
    parser.add_argument(
        "--skip-archive-check",
        action="store_true",
        help="Skip the optional ZIP provenance cross-check.",
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
    }

    sources_ok = True
    for name, path in SOURCES.items():
        exists = path.exists()
        sources_ok &= exists
        report["sources"][name] = {"path": str(path), "exists": exists}

    direct_report = verify_direct_housing_sources(
        args.housing_step.expanduser().resolve(),
        args.housing_left_stl.expanduser().resolve(),
        args.housing_right_stl.expanduser().resolve(),
    )
    report["housing_direct_sources"] = direct_report
    housing_ok = bool(direct_report["ok"])

    if not args.skip_archive_check:
        archive_report = verify_housing_archive(args.housing_archive.expanduser().resolve())
        report["housing_archive_provenance"] = archive_report
        # The archive is supplementary. A missing or mismatched ZIP is reported but
        # does not invalidate the directly verified STEP/STL source package.

    if args.export_pcb_step and SOURCES["pcb"].exists():
        report["pcb_step_export"] = export_pcb_step(
            SOURCES["pcb"], TASK1_DIR / "generated/klor1_4.step"
        )

    report["preflight_passed"] = sources_ok and housing_ok
    report["remaining_task1_work"] = [
        "derive and record PCB-to-switchplate transform",
        "derive and record PCB-to-case transform",
        "place verified Type-C STEP in Z using the real switchplate interface",
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

    return 0 if report["preflight_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
