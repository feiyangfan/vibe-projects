# Task 2D Result — Geometry Freeze Revision 4

## Status

**PASS — Task 2D revision 4 is frozen.**

Revision 4 is the first Task-2 freeze qualified against the real Type-C housing, generated PCB, 25 mm sphere, stock Konrad switchplate and stock right case in one 3D frame.

## Frozen product geometry

Unchanged:

- KLOR 1.4 MX / fixed Konrad;
- 20 keys left / 19 keys right / 39 total;
- R32 / SW20 retained;
- R33 / SW21 retained;
- R34 / SW22 / D22 removed;
- both encoders retained;
- 20 left RGB / 19 right RGB;
- MCU and TRRS stock datums;
- all nine stock PCB holes;
- stock structural axes outside the bounded trackball case modification.

## Frozen trackball placement

Canonical ball XY:

**`(15.5, -31.000147)`**

This is a `(-1,-3) mm` correction from revision 3, derived by a real-housing interference search while preserving all retained keys and PCB holes.

Frozen Type-C relations:

- housing center from ball: `(+9.165901, +0.000812)`;
- housing screw midpoint from ball: `(+6.212, 0)`;
- housing screw offsets: `(0,+7.98)` and `(0,-7.98)`;
- breakout center from ball: `(+19.212, 0)`;
- Kivipallur connector remains on +X / right side.

## Frozen PCB composition

```text
stock_board
- trackball_cavity
= trackball_board
```

The cavity is derived from the actual Type-C housing section at the PCB slab plus ball/manufacturing clearance.

The old revision-3 PMW support tongue and breakout service notch are no longer part of the PCB.

## Frozen PMW mechanical interface

Keyboard-side PMW header:

- center: **`(0, -22.022143)`**;
- F.Cu;
- 1x7, 2.54 mm pitch;
- short seven-conductor cable to the Kivipallur breakout.

The breakout itself remains on the right side of the ball.

Pin order and GPIO ownership are unchanged.

## 3D integration boundary

Task 2E additionally qualifies:

- source-backed Cherry MX plate-top to PCB-top spacing of 5.0 mm;
- actual 1.5 mm Konrad switchplate;
- actual housing STL;
- actual stock right-case STL;
- relieved switchplate;
- local downward right-case trackball pod;
- native housing M2 axes supported by pod-bottom bosses.

Qualified ball center XYZ:

`(15.5, -31.000147, 1.938015634)` mm.

Qualified ball exposure above plate:

**12.938 mm**.

The pod extends **5.462 mm below the stock case bottom**.

## Qualification

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Passing workflows include:

- Task 2B: `36376432620`
- Task 2C: `36376432637`
- Task 2D: `36376432640`
- Task 2E: `36376432664`
- Tasks 3A / 3B / 3C / 3D also pass on the same head.

## Downstream boundary

Task 3 and Task 4 may not silently:

- move the revision-4 ball/housing/breakout;
- change the real-housing-derived cavity;
- move the cabled PMW board header;
- reintroduce the rigid PMW peninsula;
- restore R34/SW22/D22;
- move retained keys or stock PCB mounting holes.
