# Task 2 Revision 3 — Trackball PCB Cavity

## Status

**PASS — revision 3 cavity implemented and frozen.**

## Problem

The revision-2 right PCB correctly places the PMW/Kivipallur connector on the right side of the 25 mm ball, but the PCB clearance is not equivalent to the KLORBall-35 mechanical design.

Revision 2 subtracts only the **2 x 22 mm breakout/service notch** from the stock KLOR PCB. The 37.6 x 30.0 mm Type-C housing envelope is generated only as a reference outline and is not subtracted from the PCB.

Consequently, substantial stock FR-4 remains under and around the trackball housing. The KLORBall-35 reference instead has a broad **open-edge cavity** around the trackball/housing and retains only a narrow right-side connector peninsula.

## Root cause

The frozen revision-2 composition is:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

There is no `trackball_cavity` subtraction.

This was a modeling error in the minimal-change assumption: the service corridor was treated as the complete PCB mechanical delta rather than one component of it.

## Revision-3 design intent

The revised board shall use KLORBall-35 **topology**, not an arbitrary larger circular hole:

1. create a large cavity open to the lower/right board edge around the Type-C housing/ball region;
2. preserve a narrow peninsula on the right for the 1x7 PMW header;
3. keep the connector on the +X/right side of the ball;
4. preserve retained keys, right encoder, MCU, TRRS, and structural holes unless a quantified mechanical conflict forces a change;
5. derive dimensions from the actual Type-C housing envelope and validate them against the checked-in KLORBall-35 Edge.Cuts.

## Frozen electrical items unaffected

- PMW: GP2 SCK, GP3 MOSI, GP4 MISO, GP9 CS;
- PMW pin order: CS, MISO, MOSI, SCK, NC/MOTION, 3V3, GND;
- MOTION remains NC / polling;
- SW22/D22/R34 remain absent;
- right RGB chain remains 19 devices;
- right encoder remains A -> GP29 and B -> GP28.

## Qualified result

Revision 3 uses an explicit ball-relative polygon with a **10.934113 mm** minimum design-space distance from the ball center to the cavity boundary.

After boolean composition with the stock board, support tongue and service slot, the regenerated production PCB measures **12.323043 mm** from the ball center to the nearest actual Edge.Cuts.

For comparison, the checked-in KLORBall-35 reference measures approximately **9.658 mm** using the inferred ball center from its J2/PMW relationship.

The left cavity lip is adapted from the KLORBall-35 reference (approximately -24.285 mm) to **-21.5 mm** relative to the ball so the retained MX R33/SW21 envelope remains clear.

Qualification head: `1a6c90f3596c2b6f648c0c1663069b5713215388`.

All Tasks 2B, 2C, 2D, 3A, 3B, 3C and regenerated 3D pass on that head.

## Gate before re-freeze

Revision 3 is complete only when:

- the generated PCB has an explicit open-edge `trackball_cavity` subtraction;
- the cavity clears the required Type-C housing footprint with an explicit manufacturing margin;
- the ball center is not covered by PCB material in the generated Edge.Cuts topology;
- the PMW header remains on a connected, manufacturable right-side support peninsula;
- retained key and structural-hole clearances pass;
- Task 2B, 2C, 2D, 3A, 3B, 3C and regenerated 3D gates are green.
