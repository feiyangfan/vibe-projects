# Task 3D Result — Right Production-Intent PCB Revision 3

## Status

**PASS — Task 3D revision 3 is complete.**

The right production PCB has been regenerated on the Task-2 revision-3 open-edge trackball cavity.

The board remains electrically complete and intentionally unrouted.

## Mechanical correction

Revision 2 placed the PMW connector correctly on the right side of the ball but left too much stock FR-4 around the trackball.

Revision 3 changes the generated board outline to:

```text
stock_board
+ pmw_support_tongue
- trackball_cavity
- breakout_service_slot
= trackball_board
```

The result now has the same mechanical topology as KLORBall-35: a broad open-edge cavity around the trackball with a narrow right-side PMW connector peninsula.

The Task-3D production validator measures the nearest generated Edge.Cuts at **12.323043 mm from the ball center**, above the frozen 9.5 mm minimum.

## Production content

Unchanged electrically:

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW matrix diodes including encoder click D18;
- 19 RGB devices;
- retained right EC11 encoder;
- 0xCB Helios rev1.0;
- MJ-4PP-9 TRRS;
- reset;
- PMW 1x7 on F.Cu;
- eight M3 + one M2 stock PCB mounting holes;
- no tracks, vias or copper zones.

SW22 / D22 / R34 remain absent and the RGB chain bypasses SW22.

## PMW interface

Unchanged:

- connector is on +X / right side of the ball;
- GP2 / pad 6 = SCK;
- GP3 / pad 7 = MOSI;
- GP4 / pad 8 = MISO;
- GP9 / pad 13 = CS;
- pad 27 = V3V3;
- MOTION = NC / polling;
- pin order = CS, MISO, MOSI, SCK, NC, V3V3, GND;
- Kivipallur mating = breakout pin N -> keyboard pin 8-N.

## Qualification

Qualification head:

`1a6c90f3596c2b6f648c0c1663069b5713215388`

Passing Task-3D workflow:

- run ID: `36090754164`
- conclusion: **success**

Artifact:

- `klor-task3d-right-production-pcb`
- artifact ID: `10846040850`
- SHA-256: `cb44b3484815952b6f167243e609583b23797054b4561bb21f4051ed254f8629`

The same qualification head passed Tasks 2B, 2C revision 3, 2D revision 3, 3A, 3B and 3C.

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze**.
