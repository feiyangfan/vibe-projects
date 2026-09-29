# Task 2C Result — Trackball Delta Revision 4

## Status

**PASS — Task 2C revision 4 is complete.**

Revision 4 supersedes the revision-3 2D-only cavity after Task 2E tested the actual Type-C housing in 3D.

## Why revision 4 was required

Revision 3 gave the nominal ball a large open PCB cavity, but the actual Type-C housing still intersected the generated PCB by approximately **158.111 mm³** at a useful installation height.

A Z-only workaround required approximately 24 mm of ball exposure above the plate and was rejected.

Task 2E found the minimum nearby clean XY placement that preserves all 19 retained right keys and all nine stock PCB holes:

```text
revision-3 ball = (16.5, -28.000147)
revision-4 ball = (15.5, -31.000147)
delta           = (-1.0, -3.0) mm
```

## Revision-4 PCB delta

The right PCB is now:

```text
stock_board
- actual_housing_and_ball_cavity
= trackball_board
```

The cavity is derived from the real Type-C housing section through the PCB slab, a 25 mm sphere and manufacturing clearance.

The obsolete rigid PMW support tongue and 2 x 22 service-notch architecture are removed.

The generated revision-4 production PCB has approximately **11.806 mm** minimum Edge.Cuts distance from the ball center and passes the full Task-2E mesh-level PCB/housing check.

## PMW interface

The Kivipallur breakout remains on the **right / +X side** of the ball:

- housing center from ball: `(+9.165901, +0.000812)`;
- breakout center from ball: `(+19.212, 0)`.

The keyboard-side PMW header is moved to reclaimed SW22 PCB area at:

`(0, -22.022143)`

It connects to the Kivipallur breakout with a short seven-conductor cable.

The electrical/physical pin contract remains:

1. CS
2. MISO
3. MOSI
4. SCK
5. NC / MOTION
6. 3V3
7. GND

and cable mapping remains breakout pin `N` to keyboard pin `8-N`.

## Preserved geometry

Revision 4 retains:

- R32 / SW20;
- R33 / SW21;
- right encoder;
- MCU and TRRS;
- all 19 active right MX positions;
- all nine stock PCB holes;
- stock geometry outside the bounded real-housing trackball delta.

R34 / SW22 / D22 remain electrically absent.

## Qualification

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Passing workflow:

- `KLOR Task 2C - trackball delta`
- run ID: `36376432637`
- conclusion: **success**

The same head passes Task 2E's full 3D integration gate.
