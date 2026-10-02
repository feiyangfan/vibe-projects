# Task 2E — 3D Trackball Mechanical Integration Revision 6

## Status

**PASS — COMPLETE.**

Task 2E places the generated Revision-6 right PCB, physical Type-C housing, 25 mm ball, stock Konrad switchplate and stock right case into one source-aligned 3D frame.

## Handedness authority

Handedness is determined from the **actual STL geometry**, not its filename.

The required right-thumb arrangement is:

```text
thumb -> opening -> ball | housing / sensor / connector -> outside-right
          -X                                              +X
```

The qualified `type_c_right.stl` mesh has:

- ball toward the housing's left side;
- opening on -X/left;
- housing bulk on +X/right.

The validator checks both the asymmetric X bounds and an upper-rim opening probe.

## Common frame

- ball center: `(15.5, -31.000147, 1.938015634)` mm;
- switchplate: `z=0..1.5 mm`;
- PCB: `z=-5.1..-3.5 mm`;
- exposed 25 mm ball cap: approximately `12.938 mm`.

## PCB/cavity

```text
stock_board - actual_housing_and_ball_cavity
```

At the frozen position:

- housing vs PCB = 0 mm³;
- sphere vs PCB = 0 mm³;
- all 19 retained right keys remain;
- all nine PCB holes remain.

## PMW interface

Housing/Kivipallur structure extends toward +X/right.

The keyboard-side 1x7 remains separate:

- center `(0, -22.022143)` mm;
- F.Cu;
- row on canonical Y;
- short seven-conductor cable to the breakout.

## Switchplate/case

The actual housing and sphere keepouts generate the local plate and case relief.

The right case uses:

- 1.5 mm pod wall/floor;
- two bottom M2 bosses;
- 3.0 mm boss outer radius;
- 100% support at both axes;
- approximately 5.462 mm downward extension below stock case.

## Physical validation

Digital fit is qualified. A physical mock-up remains required for thumb posture, opening access, ball feel, cable behavior, fasteners and desk stance.

Implementation head `c5023e227d6a766726e247d3e605949fe7b1d545` passes Task 2E run `36950226502`.
