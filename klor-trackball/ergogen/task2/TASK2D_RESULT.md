# Task 2D Result — Geometry Freeze Revision 2

## Status

**PASS — Task 2D revision 2 is frozen.**

The geometry freeze was explicitly reopened to correct trackball handedness. Revision 2 replaces the former left-side connector placement with the KLORBall-35-style right-side orientation.

## Frozen product geometry

Unchanged:

- KLOR 1.4 MX / fixed Konrad;
- 20 keys left;
- 19 keys right;
- 39 total;
- R32 / SW20 retained;
- R33 / SW21 retained;
- R34 / SW22 / D22 removed;
- left encoder retained;
- right encoder retained at its stock location;
- 20 left RGB / 19 right RGB;
- MCU, TRRS and all nine PCB mounting-hole stock positions;
- eight stock case/switchplate structural axes.

## Frozen trackball revision 2

Ball:

`(16.5, -28.000147)` in the canonical SW13 frame.

The ball moved `-5.761644 mm` in canonical X from the original Task-2 placement. Y is unchanged.

The Type-C/Kivipallur assembly is rotated to the connector-right orientation:

- housing center from ball: `(+9.165901, +0.000812)`;
- screw midpoint from ball: `(+6.212, 0)`;
- breakout center from ball: `(+19.212, 0)`;
- keyboard header center from breakout: `(-4.613622, 0)`;
- service direction: positive X.

The inward ball shift is required by the same conservative housing-envelope clearance rule used in Task 2C; a direct flip at the old ball center overlaps retained SW16.

## PMW mechanical/electrical interface

Frozen:

- keyboard header on F.Cu;
- 1x7 / 2.54 mm;
- row axis Y;
- connector on the right / +X side of the ball;
- pin 1 / CS at the positive-canonical-Y end;
- pin 7 / GND at the negative-canonical-Y end;
- pin signals remain CS, MISO, MOSI, SCK, NC_MOTION, 3V3, GND;
- Kivipallur mating remains breakout `N` to keyboard `8-N`.

Support tongue:

- center from breakout: `(-3.9444785, -0.0894995)`;
- size: `5.888957 x 18.825007 mm`;
- proven header-body overhang: approximately `18.092963 mm`.

Target PCB remains:

`stock_board + support_tongue - 2x22 service_notch`.

## Preserved mounting geometry

All stock PCB holes MH1 through MH9 remain unchanged.

The connector-right notch has approximately **3.354275 mm** clearance to the nearest edge of MH8's M3 drill, so no PCB-hole relocation is required.

Case/switchplate structural axes remain frozen at stock coordinates. Exact right-case shell relief remains a downstream case task.

## Qualification

Qualification head:

`53db19fc1d0049b4bcc4f311a69ae30ba4713313`

Passing workflow:

- `KLOR Task 2D - geometry freeze`
- run ID: `35948524848`
- conclusion: **success**

Artifact:

- `klor-task2d-frozen-geometry`
- artifact ID: `10787439172`
- SHA-256: `4d3f6e3bade8353722ebce6a229868be1b4e29fc34b04d34e93cb75dd93a585d`

The same head also passed Task 2B and Task 2C.

## Task-3 boundary

Task 3 may add electrical footprints, nets and routing intent. It may not silently move the revision-2 ball, housing, breakout, header, retained controls, mounting axes, or change the KLORBall-35-style connector handedness.
