# Task 3D Result — Right Production-Intent PCB Revision 5

## Status

**PASS — Task 3D revision 5 is complete.**

The generated right production PCB consumes the frozen Task-2 revision-5 correctly handed trackball geometry. It is electrically complete and intentionally unrouted.

## Production content

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW diodes: 19 MX + encoder click D18;
- 19 RGB devices;
- retained right EC11 encoder;
- 0xCB Helios rev1.0;
- TRRS;
- reset;
- F.Cu PMW 1x7 cabled header;
- eight M3 + one M2 stock PCB holes;
- no tracks, vias or copper zones.

SW22 / D22 / R34 remain absent.

## Revision-5 mechanical geometry

Ball center:

**`(22.0, -31.000147)`**

Correct housing orientation:

- source left STL on right keyboard half;
- opening -X / thumb side;
- housing/Kivipallur connector +X / outward.

The generated real-housing cavity has approximately **14.212 mm** XY material distance from the ball center, and Task 2E proves zero sphere/PCB and housing/PCB intersection.

## PMW board header

Canonical center:

**`(18.5, -14.5)`**

- F.Cu;
- 90° rotation;
- row axis X;
- pin 1 / CS at +X;
- pin 7 / GND at -X;
- short seven-conductor cable to the outward Kivipallur breakout.

Electrical ownership remains:

- GP2 / pad 6 -> SCK;
- GP3 / pad 7 -> MOSI;
- GP4 / pad 8 -> MISO;
- GP9 / pad 13 -> CS;
- pad 27 -> V3V3;
- MOTION -> NC / polling.

## Qualification

Implementation qualification head:

`0b704c8ff85c6b641b796813f49e78124d8e21ec`

Passing Task-3D workflow: `36697008138`.

The same head passes the Task-2E full 3D mechanical integration gate.

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze**.

Task 4 routing should remain behind the physical right-half mechanical mock-up gate.
