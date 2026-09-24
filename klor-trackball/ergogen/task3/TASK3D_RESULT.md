# Task 3D Result — Right Production-Intent PCB Revision 2

## Status

**PASS — Task 3D revision 2 is complete.**

Task 3D was reopened after the trackball handedness correction. The generated right PCB now places the PMW/Kivipallur connector on the **right / positive canonical X side of the ball**, matching the checked-in KLORBall-35 right PCB orientation.

The board remains electrically complete and intentionally unrouted.

## Qualified right-board content

Generated PCB:

`task3d_right_production.kicad_pcb`

Content:

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW matrix diodes: 19 MX + encoder click D18;
- 19 RGB devices;
- one EC11 encoder with diode-isolated push;
- one 0xCB Helios rev1.0;
- one MJ-4PP-9 TRRS connector;
- one reset switch;
- one PMW 1x7 connector on F.Cu;
- eight M3 + one M2 stock PCB mounting holes;
- no tracks, vias, or copper zones.

Routing remains Task 4.

## Revision-2 mechanical placement

Canonical ball center:

`(16.5, -28.000147)`

This is a `-5.761644 mm` inward-X shift from the former Task-2 center.

The shift is required because a direct 180 degree flip at the old center causes the conservative Type-C housing envelope to overlap retained SW16.

Revision-2 relationships:

- housing center from ball: `(+9.165901, +0.000812)`;
- breakout center from ball: `(+19.212, 0)`;
- PMW header center from breakout: `(-4.613622, 0)`;
- PMW header center: `(31.098378, -28.000147)`.

The PMW header and breakout are therefore on the right / +X side of the ball.

The conservative housing gate passes with approximately **2.580294 mm** clearance to SW16.

The 2 x 22 service notch clears stock MH8 by approximately **3.354275 mm edge-to-drill**, so all stock PCB mounting-hole positions remain unchanged.

## KLORBall-35 header orientation

The checked-in KLORBall-35 right PCB was audited directly before this revision.

KLORBall-35 J2 uses:

1. CS
2. MISO
3. MOSI
4. SCK
5. NC / MOTION
6. 3V3
7. GND

Revision 2 matches its physical direction:

- keyboard pin 1 / CS = positive canonical Y end;
- keyboard pin 7 / GND = negative canonical Y end;
- canonical PMW footprint rotation = 0 degrees.

The electrical pin assignment itself is unchanged.

The verified Kivipallur mate remains:

`breakout pin N -> keyboard pin 8-N`.

## Electrical ownership

PMW controller ownership remains:

- GP2 / Helios pad 6 -> SCK;
- GP3 / Helios pad 7 -> MOSI;
- GP4 / Helios pad 8 -> MISO;
- GP9 / Helios pad 13 -> CS;
- Helios pad 27 -> V3V3;
- MOTION -> NC / polling.

The right encoder remains:

- A -> GP29 / Helios pad 26;
- B -> GP28 / Helios pad 25.

SW22 / D22 / R34 and its RGB device remain absent. The 19-device RGB chain bypasses SW22.

## PCB outline

The board still uses:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

Revision-2 support tongue:

- center from breakout: `(-3.9444785, -0.0894995)`;
- size: `5.888957 x 18.825007 mm`;
- connector body overhang beyond the stock lower edge: approximately `18.092963 mm`.

No unrelated stock Edge.Cuts are changed.

## Qualification

Qualification head:

`53db19fc1d0049b4bcc4f311a69ae30ba4713313`

Passing Task-3D workflow:

- workflow: `KLOR Task 3D - right production PCB`
- run ID: `35948524891`
- conclusion: **success**

Artifact:

- `klor-task3d-right-production-pcb`
- artifact ID: `10787776772`
- SHA-256: `0fcd6c270e1524f043f4db30db0d5634e4b9d4794feeb0a7ab4fb6923d720f57`

The same qualification head also passed:

- Task 2B;
- Task 2C revision 2;
- Task 2D revision 2;
- Task 3A;
- Task 3B;
- Task 3C.

The Task-3D gate verifies deterministic generation, exact footprint counts, matrix/RGB contracts, connector-right PMW geometry and physical direction, SPI/3V3 endpoint ownership, stock mounting holes, and the intentionally unrouted state.

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze**.
