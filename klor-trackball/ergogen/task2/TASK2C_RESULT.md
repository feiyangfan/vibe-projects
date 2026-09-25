# Task 2C Result — Trackball Delta Revision 3

## Status

**PASS — Task 2C revision 3 is complete.**

Revision 3 preserves the revision-2 connector-right Type-C/Kivipallur placement and corrects the PCB clearance topology around the trackball.

## Corrected PCB delta

Revision 2 incorrectly treated the 2 x 22 mm breakout/service corridor as the complete PCB clearance feature. That left substantial stock FR-4 under and around the trackball.

Revision 3 uses:

```text
stock_board
+ pmw_support_tongue
- trackball_cavity
- breakout_service_slot
= trackball_board
```

The new `trackball_cavity` is an open-edge polygon based on the checked-in KLORBall-35 right-PCB topology.

## Cavity geometry

Ball-relative cavity vertices in canonical coordinates:

```text
(-21.50, +13.00)
( -5.00, +12.94)
( +9.93, +12.36)
(+11.85, +10.19)
( +9.31, -19.37)
(+11.17, -21.54)
(+11.17, -40.00)
(-21.50, -40.00)
```

The KLORBall-35 reference left lip is approximately `-24.285 mm` from the inferred ball center. Revision 3 pulls that lip inward to `-21.5 mm` to preserve the retained MX R33/SW21 envelope.

The explicit cavity polygon gives **10.934113 mm** minimum ball-center-to-cavity-boundary distance. The generated production board's nearest actual Edge.Cuts is **12.323043 mm** from the ball center. The corresponding KLORBall-35 reference measurement is approximately **9.658 mm**.

The ball center lies inside the removed cavity. The PMW header, R33/SW21 and stock MH8 remain outside it.

## Unchanged revision-2 placement

- ball center: `(16.5, -28.000147)`;
- housing center from ball: `(+9.165901, +0.000812)`;
- breakout center from ball: `(+19.212, 0)`;
- PMW header center from breakout: `(-4.613622, 0)`;
- connector remains on +X / right side of the ball;
- PMW physical pin direction remains KLORBall-35-compatible.

The limiting conservative retained-key/housing clearance remains SW16 at approximately **2.580294 mm**.

The 2 x 22 service notch still clears MH8 by approximately **3.354275 mm edge-to-drill**.

## Qualification

Qualification head:

`1a6c90f3596c2b6f648c0c1663069b5713215388`

Passing workflow:

- `KLOR Task 2C - trackball delta`
- run ID: `36090754209`
- conclusion: **success**

Artifact:

- `klor-task2c-trackball-geometry`
- artifact ID: `10845079830`
- SHA-256: `03cc151e9558abd916f74acd277e2d2d3d913078c4aff299e87d314510822dba`

Task 2B also passed on the same head.
