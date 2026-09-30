# Task 2E — 3D Trackball Mechanical Integration Revision 5

## Status

**PASS — COMPLETE.**

Task 2E places the generated revision-5 right PCB, correctly handed Type-C housing, 25 mm sphere, Konrad switchplate and stock right case in one source-aligned 3D frame.

## Handedness correction

Revision 4 used `type_c_right.stl` and therefore validated the wrong physical opening/connector direction.

Revision 5 uses `type_c_left.stl` on the right keyboard half:

```text
thumb side / -X  <- opening | ball | housing / connector ->  +X / outside
```

The validator checks the source mesh X bounds so this error cannot silently recur.

## Frozen common frame

- ball center: `(22.0, -31.000147, 1.938015634)` mm;
- plate: `z=0..1.5 mm`;
- PCB: `z=-5.1..-3.5 mm`;
- 25 mm ball exposure: approximately `12.938 mm`.

The Rev-4-qualified Z is intentionally preserved. Revision 5 corrects handedness and XY clearance without using a wider PCB cavity as an excuse to lower the ball.

## PCB/cavity

The PCB remains:

```text
stock_board - actual_housing_and_ball_cavity
```

At the frozen position:

- PCB XY material distance from ball center: about **14.212 mm**;
- sphere/PCB intersection: **0**;
- housing/PCB intersection: **0**;
- all 19 retained right keys remain;
- all nine PCB holes remain;
- conservative rectangular housing/key margin: about **2.683 mm**.

## PMW header

The outward housing/Kivipallur connector and keyboard PCB header are separate interfaces.

Board header:

- `(18.5, -14.5)` mm;
- 1x7, 2.54 mm pitch;
- F.Cu;
- 90° rotation;
- row along canonical X;
- cabled to the breakout.

## Switchplate/case

Actual housing and sphere keepouts are subtracted from the stock switchplate and case.

The right case gains the same local mounting concept qualified in Rev 4:

- 1.5 mm pod wall/floor;
- two bottom M2 bosses;
- 3.0 mm boss outer radius;
- 100% support at both qualified axes;
- approximately 5.462 mm local downward extension.

## Ergonomic limitation

Digital fit is not subjective comfort.

The correctly handed housing moves the ball outward. R33/SW21 is now approximately **40.608 mm center-to-center** from the ball. That distance, the 12.938 mm exposed cap, and the local pod must be tested with a physical right-half mock-up before production routing/fabrication is treated as mechanically final.

## Qualification

Implementation head `0b704c8ff85c6b641b796813f49e78124d8e21ec` passes Task 2E run `36697008540` and the dependent Task 2B/2C/2D/3D gates.
