# Task 4B Result — Regeneration-Safe Routing Mechanism Proof

## Status

**PASS — Task 4B is complete.**

Task 4B proves that routing can be derived from generated electrical geometry rather than preserved KiCad object identity.

## Representative routed slice

The proof routes two real nets on the generated left production PCB:

- `SW1_TO_D1` — matrix class;
- `RGB_SW1_TO_SW2` — RGB-data class.

Both are two-endpoint nets. The router discovers their endpoints from the generated board's **net names and pad coordinates**.

The route algorithm is deliberately simple for this proof: deterministic direct 45-degree/two-endpoint routing on the Task-4A left local layer, B.Cu.

## Identity model

Allowed routing inputs:

- net name;
- net ID resolved from that name in the current generated board;
- current footprint/pad geometry;
- Task-4A routing-class rules.

Forbidden dependencies:

- lookup by an existing KiCad UUID;
- lookup by generated object identity;
- copied absolute route coordinates.

KiCad segment UUIDs are generated deterministically as output metadata. They are never used to find or preserve tracks.

## Determinism proof

CI performs two clean Ergogen generations, routes both independently, then byte-compares the routed proof boards.

The generated production pair and the routed proof are both deterministic.

## Upstream-change proof

The CI fixture modifies source-level canonical placement before regeneration:

- `d1.x += 1.25 mm`;
- `sw2.x += 1.25 mm`.

It then regenerates the left PCB and runs the same router with no manual track edits.

The validator proves:

- the affected generated pad endpoints moved;
- both selected proof routes changed accordingly;
- the new routes still terminate exactly on the regenerated pads;
- Task-4A width/layer rules remain satisfied.

The production `config.yaml` is restored byte-for-byte after the fixture.

## Qualification

First passing qualification:

- workflow: `KLOR Task 4B - routing mechanism proof`;
- run ID: `37724448292`;
- head: `9b331eb74dd8748ca310a5bb03c0bfe5f3d57258`;
- result: **success**;
- artifact: `klor-task4b-routing-proof`;
- artifact ID: `11527455924`;
- artifact SHA-256: `2d446d9a978db2b887fd2454f60f455e4c5eb0eb2f1652024789161b6b17d40b`.

The workflow also re-ran Task 4A before routing.

## Engineering conclusion

The project now has a proven routing primitive that survives a controlled upstream geometry change without UUID-based mutation or manual track repair.

This does **not** mean the complete keyboard is routed. It establishes the architecture that Task 4C–4E can scale.

## Next

Proceed to **Task 4C — route the complete left PCB** using the proven net-name/pad-geometry routing approach.
