#!/usr/bin/env python3
"""Task 3A audit: verify the non-destructive KiCad derivative baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
STOCK = ROOT / "klor1.4/PCB/klor1_4"
DERIV = ROOT / "PCB/konrad_trackball"

EXPECTED_STOCK_GIT_OBJECTS = {
    "klor1_4.kicad_pcb": "3dea93bc4266541e9ca85eebc70e4b8c851afc11",
    "klor1_4.kicad_sch": "4f68892c9d13ffe4200587708eeb4c43ee2b652b",
    "klor1_4.kicad_dru": "c42eb3c41e311ef8d41bba80710107bf6b5786f1",
    "klor1_4.kicad_pro": "a48391de09297c3afd7d18e588ff6de2b5c0ce88",
    "klor1_4.round-tracks-config": "6b6b9154c4397dd3b3a8ac25ca415e6170856d97",
    "KLORlib.kicad_sym": "3a68ac40933b283d2df8ef15b01a115af9f4b18c",
    "fp-lib-table": "32ec98e52c426b65f099c75f4b3edc066ba6b1ee",
    "sym-lib-table": "edfcf128a86d83a1df5b9abfba8ce68982cba6d0",
    "KLOR.pretty": "79ffad5adf9b695e69f36560ef7fde1af50392c2",
}

EXACT_FILE_PAIRS = {
    "klor1_4.kicad_pcb": "konrad_trackball.kicad_pcb",
    "klor1_4.kicad_sch": "konrad_trackball.kicad_sch",
    "klor1_4.kicad_dru": "konrad_trackball.kicad_dru",
    "klor1_4.round-tracks-config": "konrad_trackball.round-tracks-config",
    "KLORlib.kicad_sym": "KLORlib.kicad_sym",
    "fp-lib-table": "fp-lib-table",
    "sym-lib-table": "sym-lib-table",
}


def git_object(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    proc = subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git rev-parse failed for {rel}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    checks: dict[str, bool] = {}
    evidence: dict[str, object] = {}

    checks["stock_directory_exists"] = STOCK.is_dir()
    checks["derivative_directory_exists"] = DERIV.is_dir()

    source_objects = {}
    for rel, expected in EXPECTED_STOCK_GIT_OBJECTS.items():
        p = STOCK / rel
        actual = git_object(p)
        source_objects[rel] = {"expected": expected, "actual": actual}
        key = rel.replace(".", "_").replace("/", "_")
        checks[f"stock_object_{key}_locked"] = actual == expected
    evidence["stock_git_objects"] = source_objects

    exact_pairs = {}
    for stock_name, deriv_name in EXACT_FILE_PAIRS.items():
        stock_path = STOCK / stock_name
        deriv_path = DERIV / deriv_name
        identical = stock_path.read_bytes() == deriv_path.read_bytes()
        exact_pairs[stock_name] = {
            "stock": str(stock_path.relative_to(ROOT)),
            "derivative": str(deriv_path.relative_to(ROOT)),
            "identical": identical,
        }
        checks[f"exact_copy_{deriv_name.replace('.', '_')}"] = identical
    evidence["exact_file_pairs"] = exact_pairs

    stock_fp = STOCK / "KLOR.pretty"
    deriv_fp = DERIV / "KLOR.pretty"
    stock_fp_files = sorted(p.name for p in stock_fp.glob("*.kicad_mod"))
    deriv_fp_files = sorted(p.name for p in deriv_fp.glob("*.kicad_mod"))
    checks["footprint_file_set_identical"] = stock_fp_files == deriv_fp_files
    stock_fp_object = git_object(stock_fp)
    deriv_fp_object = git_object(deriv_fp)
    checks["footprint_tree_git_object_identical"] = stock_fp_object == deriv_fp_object
    evidence["footprint_library"] = {
        "stock_tree": stock_fp_object,
        "derivative_tree": deriv_fp_object,
        "files": deriv_fp_files,
    }

    stock_pro = json.loads((STOCK / "klor1_4.kicad_pro").read_text(encoding="utf-8"))
    deriv_pro = json.loads((DERIV / "konrad_trackball.kicad_pro").read_text(encoding="utf-8"))
    checks["stock_project_metadata_filename_intact"] = (
        stock_pro.get("meta", {}).get("filename") == "klor1_4.kicad_pro"
    )
    checks["derivative_project_metadata_filename"] = (
        deriv_pro.get("meta", {}).get("filename") == "konrad_trackball.kicad_pro"
    )
    normalized_deriv = json.loads(json.dumps(deriv_pro))
    normalized_deriv.setdefault("meta", {})["filename"] = "klor1_4.kicad_pro"
    checks["project_content_diff_only_metadata_filename"] = normalized_deriv == stock_pro

    fp_table = (DERIV / "fp-lib-table").read_text(encoding="utf-8")
    sym_table = (DERIV / "sym-lib-table").read_text(encoding="utf-8")
    checks["footprint_library_is_project_local"] = "${KIPRJMOD}/KLOR.pretty" in fp_table
    checks["symbol_library_is_project_local"] = "${KIPRJMOD}/KLORlib.kicad_sym" in sym_table

    checks["no_inherited_gerbers"] = not (DERIV / "gerbers").exists()

    expected_project_files = {
        "konrad_trackball.kicad_pro",
        "konrad_trackball.kicad_sch",
        "konrad_trackball.kicad_pcb",
        "konrad_trackball.kicad_dru",
        "konrad_trackball.round-tracks-config",
        "KLORlib.kicad_sym",
        "fp-lib-table",
        "sym-lib-table",
        "README.md",
    }
    present_files = {p.name for p in DERIV.iterdir() if p.is_file()}
    checks["required_project_files_present"] = expected_project_files.issubset(present_files)

    pcb = (DERIV / "konrad_trackball.kicad_pcb").read_text(encoding="utf-8", errors="ignore")
    sch = (DERIV / "konrad_trackball.kicad_sch").read_text(encoding="utf-8", errors="ignore")
    checks["task3b_not_started_sw22_still_present"] = 'Reference" "SW22"' in pcb
    checks["task3b_not_started_d22_still_present"] = (
        'Reference" "D22"' in pcb or 'Reference" "D22"' in sch
    )
    checks["derivative_readme_present"] = (DERIV / "README.md").is_file()

    result = {
        "task": "3A",
        "status": "complete" if all(checks.values()) else "failed",
        "stock_project": str(STOCK.relative_to(ROOT)),
        "derivative_project": str(DERIV.relative_to(ROOT)),
        "project_basename": "konrad_trackball",
        "schematic_driven": True,
        "fabrication_outputs_copied": False,
        "evidence": evidence,
        "checks": checks,
    }

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
