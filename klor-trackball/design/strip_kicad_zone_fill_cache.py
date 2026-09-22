#!/usr/bin/env python3
"""Strip regenerable KiCad cached zone-fill polygons from .kicad_pcb files."""

from __future__ import annotations

import argparse
from pathlib import Path


TOKEN = "(filled_polygon"


def block_end(text: str, start: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced KiCad s-expression")


def strip_cached_zone_fills(text: str) -> tuple[str, int]:
    out: list[str] = []
    cursor = 0
    removed = 0
    while True:
        marker = text.find(TOKEN, cursor)
        if marker < 0:
            out.append(text[cursor:])
            break

        start = marker
        line_start = text.rfind("\n", cursor, marker) + 1
        if not text[line_start:marker].strip():
            start = line_start

        end = block_end(text, marker)
        if text.startswith("\r\n", end):
            end += 2
        elif end < len(text) and text[end] == "\n":
            end += 1

        out.append(text[cursor:start])
        cursor = end
        removed += 1

    return "".join(out), removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pcb", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true", help="fail if cached fills are present")
    args = parser.parse_args()

    failed = False
    for path in args.pcb:
        original = path.read_text(encoding="utf-8")
        normalized, removed = strip_cached_zone_fills(original)

        if args.check:
            print(f"{path}: cached filled_polygon blocks={removed}")
            failed |= removed != 0
            continue

        if removed:
            path.write_text(normalized, encoding="utf-8")
        print(f"{path}: removed={removed}, bytes={len(original)}->{len(normalized)}")

    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
