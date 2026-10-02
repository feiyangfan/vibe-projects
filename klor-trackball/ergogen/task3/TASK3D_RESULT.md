# Task 3D Result — Right Production-Intent PCB Revision 6

## Status

**PASS — Task 3D revision 6 is complete.**

The right production PCB consumes the frozen Revision-6 mesh-verified trackball geometry. It remains electrically complete and intentionally unrouted.

## Production content

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW diodes: 19 MX + encoder click D18;
- 19 RGB devices;
- retained right EC11 encoder;
- 0xCB Helios rev1.0;
- TRRS;
- reset;
- one F.Cu PMW 1x7 cabled header;
- eight M3 + one M2 stock PCB mounting holes;
- no tracks, vias or copper zones.

SW22 / D22 / R34 remain absent.

## Revision-6 mechanical geometry

Ball center:

**`(15.5, -31.000147)` mm**

Physical housing:

- source `type_c_right.stl`;
- ball on left side of housing;
- access opening -X / left;
- housing bulk +X / right;
- handedness independently proven in Task 2E from mesh geometry.

Task 2E proves:

- sphere vs PCB = **0 mm³**;
- actual housing vs PCB = **0 mm³**.

## PMW board header

Canonical center:

**`(0, -22.022143)`**

- F.Cu;
- 2.54 mm pitch;
- row on canonical Y;
- pin 1 / CS at +Y;
- pin 7 / GND at -Y;
- short seven-conductor cable to Kivipallur breakout.

Electrical ownership remains:

- GP2 / pad 6 -> SCK;
- GP3 / pad 7 -> MOSI;
- GP4 / pad 8 -> MISO;
- GP9 / pad 13 -> CS;
- pad 27 -> V3V3;
- MOTION -> NC / polling.

## Qualification

Implementation head: `c5023e227d6a766726e247d3e605949fe7b1d545`

Passing Task-3D workflow: `36950226512`.

The same head passes the full Task-2E mesh-handedness and 3D mechanical integration gate.

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze**.

Keep Task 4 production-final routing behind the physical right-half mock-up gate.
