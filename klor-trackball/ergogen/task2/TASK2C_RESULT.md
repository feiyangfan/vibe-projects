# Task 2C Result — Trackball Delta Revision 6

## Status

**PASS — Task 2C revision 6 is complete.**

Revision 6 restores the Revision-4 geometry after proving the physical housing handedness from the actual STL mesh.

## Trackball delta

Ball center:

**`(15.5, -31.000147)` mm**

Housing source:

**`keyball_trackball_case_25mm_type_c_right.stl`**

Frozen relations:

- ball is on the **left side of the housing**;
- access opening is **-X / left / thumb side**;
- housing bulk is **+X / right / outward**;
- housing center from ball: `(+9.165901, +0.000812)` mm;
- screw midpoint from ball: `(+6.212, 0)` mm;
- breakout center from ball: `(+19.212, 0)` mm.

## PCB delta

```text
stock_board
- actual_housing_and_ball_cavity
= trackball_board
```

The cavity is the previously qualified real-housing/ball cavity from Revision 4.

Preserved:

- all 19 retained right MX keys;
- R32 / SW20;
- R33 / SW21;
- right encoder;
- MCU and TRRS datums;
- all nine stock PCB holes.

R34 / SW22 / D22 remain absent.

## PMW board interface

Keyboard-side 1x7:

- center: **`(0, -22.022143)` mm**;
- F.Cu;
- 2.54 mm pitch;
- row on canonical Y;
- pin 1 / CS at +Y;
- pin 7 / GND at -Y;
- short seven-conductor cable to the outward/right Kivipallur breakout.

The breakout pin-`N` to keyboard pin-`8-N` mating rule is unchanged.

## Ergonomic geometry

Nearest retained key center:

- R33 / SW21: **34.196 mm** from the ball.

This is substantially closer than the invalid Revision-5 placement and returns to the previously qualified minimum-change geometry.

## Qualification

Implementation head: `c5023e227d6a766726e247d3e605949fe7b1d545`

Passing Task-2C workflow: `36950226630`.

The same head passes Task 2D, Task 2E and Task 3D.
