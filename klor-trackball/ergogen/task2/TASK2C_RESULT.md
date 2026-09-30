# Task 2C Result — Trackball Delta Revision 5

## Status

**PASS — Task 2C revision 5 is complete.**

Revision 5 supersedes revision 4 because revision 4 qualified the wrong physical Type-C housing handedness.

## Frozen trackball delta

Ball center:

**`(22.0, -31.000147)` mm**

Correctly handed housing:

- source: `keyball_trackball_case_25mm_type_c_left.stl`;
- opening: -X / inward toward the thumb;
- connector: +X / outward;
- housing center from ball: `(-9.165901, +0.000812)` mm;
- screw midpoint from ball: `(-6.212, 0)` mm.

Board composition remains:

```text
stock_board
- correctly_handed_actual_housing_and_ball_cavity
= trackball_board
```

All 19 retained right keys and all nine stock PCB holes remain.

## PMW board header

The Kivipallur breakout remains outward on +X, but the board header is separate and cabled.

Keyboard-side 1x7:

- center: **`(18.5, -14.5)`**;
- F.Cu;
- 2.54 mm pitch;
- 90° canonical rotation;
- row axis: X;
- pin 1 / CS at +X;
- pin 7 / GND at -X.

The electrical pin order remains CS, MISO, MOSI, SCK, NC/MOTION, 3V3, GND.

## Clearance

The selected placement keeps the historical conservative housing/key rule and also passes the real-mesh gate:

- conservative rectangular housing/key gap: about **2.683 mm**;
- nearest retained key center: SW15, about **33.779 mm**;
- Task 2E housing vs PCB: **0 mm³**;
- Task 2E sphere vs PCB: **0 mm³**.

## Qualification

Implementation qualification head:

`0b704c8ff85c6b641b796813f49e78124d8e21ec`

Passing Task-2C workflow: `36697008095`.

The same head passes Task 2D, Task 2E and Task 3D.
