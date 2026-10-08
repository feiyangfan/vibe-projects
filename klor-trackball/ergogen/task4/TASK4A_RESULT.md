# Task 4A Result — Routing Rules and Net Classes

## Status

**PASS — Task 4A is complete.**

Task 4A freezes the routing/manufacturing envelope before any new copper is added.

## Frozen routing envelope

Board assumptions:

- 2-layer FR-4;
- 1.6 mm finished thickness;
- 1 oz outer copper / 0.035 mm copper thickness;
- F.Cu and B.Cu available for routing;
- ordinary through vias only; blind/buried vias, microvias and via-in-pad are forbidden.

Global routing rules:

- different-net clearance: **0.20 mm**;
- routed-edge copper clearance: **0.30 mm**;
- track-to-NPTH-hole clearance: **0.254 mm**;
- track-to-PTH-hole clearance: **0.35 mm**;
- via hole-to-hole clearance: **0.50 mm**;
- preferred routing corners: 45 degree;
- standard via: **0.45 / 0.30 mm** diameter/drill;
- power/ground via: **0.60 / 0.30 mm** diameter/drill.

The standard via is intentionally larger than stock KLOR's observed 0.40/0.30 mm via. The resulting 0.075 mm annular width satisfies the stock KLOR custom-rule minimum while preserving compact routing.

## Net classes

| Class | Width | Clearance | Via |
| --- | ---: | ---: | --- |
| matrix | 0.254 mm | 0.20 mm | standard |
| RGB data | 0.254 mm | 0.20 mm | standard |
| encoder/reset control | 0.254 mm | 0.20 mm | standard |
| split serial | 0.254 mm | 0.20 mm | standard |
| PMW3360 SPI | 0.254 mm | 0.20 mm | standard |
| RAW_5V / V3V3 | 0.381 mm | 0.20 mm | power |
| GND trace fallback | 0.381 mm | 0.20 mm | power |

GND uses zones on both copper layers, with routing traces only when required.

## Layer policy

- left local/component-side routing preference: **B.Cu**;
- right local/component-side routing preference: **F.Cu**;
- both layers remain available;
- unnecessary layer transitions should be minimized;
- ground-return continuity takes priority over cosmetic layer consistency.

PMW3360 SPI is right-only, prefers F.Cu, requires no controlled-impedance or length-matching treatment, and should be kept short/direct with minimal vias and nearby ground return.

## Evidence

Stock KLOR project settings freeze the reference values:

- default track: 0.254 mm;
- power track: 0.381 mm;
- default clearance: 0.20 mm;
- stock via: 0.40/0.30 mm.

The checked-in stock routed board was also parsed directly and uses only 0.254/0.381 mm traces and 0.40/0.30 mm vias.

The selected Rev-1 fabrication reference was checked against JLCPCB's rigid-PCB capability page on 2026-10-08. Task-4 values stay above the referenced manufacturing minima; those minima are evidence only and do not permit later tasks to shrink below this contract.

## Generated-net classification

The validator parses both generated Task-3 boards and requires every named electrical net to map to exactly one Task-4 routing class.

It also enforces:

- no PMW nets on the left;
- exactly PMW_SCK/MOSI/MISO/CS on the right;
- no tracks, vias, or zones added by Task 4A;
- Task 3E pair-level freeze still passes.

## Qualification

First passing run:

- workflow: `KLOR Task 4A - routing rules`;
- run ID: `37723390423`;
- head: `687f3c327de442781a2aaa62fc59456d12cee307`;
- result: **success**.

The workflow regenerated the Task-3 pair twice, proved deterministic output, re-ran Task 3E, and passed the Task-4A routing-contract validator.

## Next

Proceed to **Task 4B — prove the regeneration-safe routing mechanism**.

Task 4B should route only a representative slice first. Bulk left/right routing must not begin until that mechanism survives a controlled regeneration/geometry-change test.
