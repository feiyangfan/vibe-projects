# Task 2D Result — Geometry Freeze Revision 3

## Status

**PASS — Task 2D revision 3 is frozen.**

Revision 3 supersedes the revision-2 PCB cavity assumption. Product controls, trackball placement, connector handedness and electrical interface are unchanged; the right-PCB mechanical clearance now includes an explicit KLORBall-35-style open-edge cavity.

## Frozen product geometry

- KLOR 1.4 MX / fixed Konrad;
- 20 keys left / 19 keys right / 39 total;
- R32 / SW20 retained;
- R33 / SW21 retained;
- R34 / SW22 / D22 removed;
- both encoders retained;
- 20 left RGB / 19 right RGB;
- MCU, TRRS and all nine PCB mounting-hole stock positions retained;
- eight stock case/switchplate structural axes retained.

## Frozen trackball placement

Ball center remains:

`(16.5, -28.000147)`

Connector-right relationships remain:

- housing center from ball: `(+9.165901, +0.000812)`;
- screw midpoint from ball: `(+6.212, 0)`;
- breakout center from ball: `(+19.212, 0)`;
- PMW header center from breakout: `(-4.613622, 0)`.

PMW physical pin direction and mating rule remain unchanged from revision 2.

## Frozen PCB composition

```text
stock_board
+ pmw_support_tongue
- trackball_cavity
- breakout_service_slot
= trackball_board
```

The cavity is explicitly open to the lower edge. It removes the ball/housing region while retaining the right-side PMW peninsula.

Frozen cavity ball-relative vertices:

```text
[-21.5, 13.0]
[-5.0, 12.94]
[9.93, 12.36]
[11.85, 10.19]
[9.31, -19.37]
[11.17, -21.54]
[11.17, -40.0]
[-21.5, -40.0]
```

Minimum design gate: **9.5 mm** ball-center-to-cavity-edge.

Qualified cavity polygon: **10.934113 mm**.

Qualified generated production Edge.Cuts: **12.323043 mm** from ball center.

KLORBall-35 reference measurement: approximately **9.658 mm**.

## Qualification

Qualification head:

`1a6c90f3596c2b6f648c0c1663069b5713215388`

Passing workflow:

- `KLOR Task 2D - geometry freeze`
- run ID: `36090754218`
- conclusion: **success**

Artifact:

- `klor-task2d-frozen-geometry`
- artifact ID: `10845566291`
- SHA-256: `daa6d05baa123d6cc12ddaf840ce49cfa8f13b1733a04d329d71570a64d87182`

Task 2B and revision-3 Task 2C also pass on the same head.

## Task-3 boundary

Task 3 may add electrical implementation/routing detail but may not silently move or resize the frozen cavity, move the ball/housing/breakout/header, change connector handedness, or move retained controls/structural axes.
