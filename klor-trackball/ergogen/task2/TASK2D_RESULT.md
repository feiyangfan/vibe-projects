# Task 2D Result — Geometry Freeze Revision 6

## Status

**PASS — Task 2D revision 6 is frozen.**

Revision 6 is the canonical geometry. It is geometrically equivalent to Revision 4, with additional mesh-derived handedness validation.

## Frozen product geometry

- KLOR 1.4 MX / fixed Konrad;
- 20 keys left / 19 keys right / 39 total;
- R32 / SW20 retained;
- R33 / SW21 retained;
- R34 / SW22 / D22 removed;
- both encoders retained;
- all nine stock PCB holes retained;
- MCU and TRRS stock datums retained.

## Frozen trackball placement

Canonical ball XY:

**`(15.5, -31.000147)` mm**

Qualified common-frame XYZ:

**`(15.5, -31.000147, 1.938015634)` mm**

Ball exposure above plate:

**12.938 mm**

## Frozen physical handedness

Source: `keyball_trackball_case_25mm_type_c_right.stl`.

The actual mesh—not the filename—proves:

- ball toward housing **left**;
- access opening **-X / left**;
- housing bulk **+X / right**;
- local X bounds about `[-9.631, +27.963]` mm;
- upper-rim -X/+X vertex ratio about `0.238`.

Frozen datums:

- housing center from ball: `(+9.165901, +0.000812)`;
- screw midpoint from ball: `(+6.212, 0)`;
- screw offsets: `(0,+7.98)`, `(0,-7.98)`;
- breakout center from ball: `(+19.212, 0)`.

## Frozen PMW board interface

Keyboard-side cabled 1x7:

- center: **`(0, -22.022143)`**;
- F.Cu;
- row on canonical Y;
- pin 1 at +Y;
- pin 7 at -Y.

## 3D qualification boundary

Task 2E proves zero meaningful sphere/housing collision with the generated PCB, relieved plate, and relieved case.

The local case pod still extends about **5.462 mm** below the stock case bottom and provides two supported M2 mounting bosses.

## Change boundary

Downstream work may not silently:

- change housing mesh/handedness;
- move ball, housing, breakout, or housing screw datums;
- change the real-housing-derived cavity;
- move or rotate the board-side PMW header;
- restore R34/SW22/D22;
- move retained keys or stock PCB holes.

## Qualification

Implementation head: `c5023e227d6a766726e247d3e605949fe7b1d545`

Passing Task-2D workflow: `36950226491`.
