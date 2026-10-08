#!/usr/bin/env python3
"""Create the ephemeral Task 4B upstream-geometry perturbation fixture."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ERGOGEN = HERE.parents[1]
PROOF = ERGOGEN / "task4/task4b-routing-proof.yaml"


def replace_zone_shift(text: str, zone: str, axis: str, delta: float) -> str:
    pattern = re.compile(
        rf"(?m)^(    {re.escape(zone)}:\n      anchor:\n        shift: \[)"
        rf"([-\d.]+)(, )([-\d.]+)(\])$"
    )
    m = pattern.search(text)
    if not m:
        raise AssertionError(f"could not locate direct shift for point {zone}")
    x, y = float(m.group(2)), float(m.group(4))
    if axis == "x":
        x += delta
    elif axis == "y":
        y += delta
    else:
        raise AssertionError(f"unsupported axis {axis}")
    replacement = f"{m.group(1)}{x:.6f}{m.group(3)}{y:.6f}{m.group(5)}"
    return text[:m.start()] + replacement + text[m.end():]


def main():
    if len(sys.argv) != 3:
        raise AssertionError("usage: make_task4b_fixture.py INPUT_CONFIG OUTPUT_CONFIG")
    src, dst = map(Path, sys.argv[1:])
    proof = yaml.safe_load(PROOF.read_text(encoding="utf-8"))
    text = src.read_text(encoding="utf-8")
    for zone, spec in proof["perturbation_fixture"]["changes"].items():
        text = replace_zone_shift(text, zone, spec["axis"], float(spec["delta"]))
    dst.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
