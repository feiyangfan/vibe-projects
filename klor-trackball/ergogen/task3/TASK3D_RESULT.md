# Task 3D Result — Right Production-Intent PCB Revision 4

## Status

**PASS — Task 3D revision 4 is complete.**

The generated right production PCB now consumes the Task-2 revision-4 geometry qualified by the full Task-2E 3D mechanical integration gate.

It remains electrically complete and intentionally unrouted.

## Production content

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW matrix diodes: 19 MX + encoder click D18;
- 19 RGB devices;
- retained right EC11 encoder;
- 0xCB Helios rev1.0;
- MJ-4PP-9 TRRS;
- reset;
- one F.Cu PMW 1x7 keyboard-side cable header;
- eight M3 + one M2 stock PCB mounting holes;
- no tracks, vias or copper zones.

SW22 / D22 / R34 remain absent. The right RGB chain contains exactly 19 devices.

## Revision-4 mechanical geometry

Ball center:

`(15.5, -31.000147)`

Board composition:

```text
stock_board
- actual_housing_and_ball_cavity
= trackball_board
```

The generated PCB's nearest Edge.Cuts is approximately **11.806 mm** from the ball center.

Task 2E proves:

- 25 mm sphere vs PCB = 0 mm³;
- actual Type-C housing vs PCB = 0 mm³.

## PMW interface

The Kivipallur breakout/connector remains on the **right / +X side of the ball**.

Because the actual housing occupies the old rigid peninsula, the keyboard-side 1x7 is instead located at canonical:

**`(0, -22.022143)`**

and connects via a short seven-conductor cable.

Electrical ownership is unchanged:

- GP2 / Helios pad 6 -> SCK;
- GP3 / pad 7 -> MOSI;
- GP4 / pad 8 -> MISO;
- GP9 / pad 13 -> CS;
- pad 27 -> V3V3;
- MOTION -> NC / polling.

Physical cable-header order remains CS, MISO, MOSI, SCK, NC, 3V3, GND.

## Qualification

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Passing workflow:

- `KLOR Task 3D - right production PCB`
- run ID: `36376432835`
- conclusion: **success**

The same head also passes Task 2E's real 3D integration gate.

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze** after revision 4 is merged.
