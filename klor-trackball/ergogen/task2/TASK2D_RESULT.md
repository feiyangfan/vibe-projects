# Task 2D Result — Geometry Freeze Revision 5

## Status

**PASS — Task 2D revision 5 is frozen.**

Revision 5 is the canonical geometry after correcting the physical handedness of the Type-C housing.

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
- all nine stock PCB holes.

## Frozen trackball geometry

Ball center XY:

**`(22.0, -31.000147)` mm**

Qualified common-frame XYZ:

**`(22.0, -31.000147, 1.938015634)` mm**

Ball exposure above plate:

**12.938 mm**

Housing:

- source variant: checked-in **left STL** for the right keyboard half;
- opening: -X / thumb side;
- connector: +X / outward;
- center from ball: `(-9.165901, +0.000812)`;
- screw midpoint from ball: `(-6.212, 0)`;
- screw offsets: `(0,+7.98)`, `(0,-7.98)`.

## Frozen PMW mechanical interface

Kivipallur/housing connector: **+X / outward**.

Keyboard-side cabled 1x7:

- center: **`(18.5, -14.5)`**;
- F.Cu;
- 90° rotation;
- row axis X;
- pin 1 at +X, pin 7 at -X;
- cable mapping: breakout pin `N` -> keyboard pin `8-N`.

## 3D integration

Task 2E proves:

- sphere vs PCB: **0 mm³**;
- housing vs PCB: **0 mm³**;
- sphere vs relieved plate: **0 mm³**;
- housing vs relieved plate: numerical residue `6.47e-8 mm³`;
- sphere vs relieved case: **0 mm³**;
- housing vs relieved case: numerical residue `4.40e-7 mm³`.

The local case pod extends approximately **5.462 mm** below the stock-case bottom. Both M2 boss support checks are 100%.

## Downstream boundary

Task 3/4 may not silently:

- change housing handedness;
- move the ball/housing/breakout;
- change the actual-housing-derived cavity;
- move or rotate the board-side PMW header;
- restore R34/SW22/D22;
- move retained keys or stock PCB holes.

## Qualification

Implementation qualification head:

`0b704c8ff85c6b641b796813f49e78124d8e21ec`

Passing Task-2D workflow: `36697008291`.
