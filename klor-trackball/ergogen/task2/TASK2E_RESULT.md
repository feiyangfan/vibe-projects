# Task 2E Result — Full 3D Mechanical Integration Revision 6

## Status

**PASS — COMPLETE.**

Revision 6 requalifies the previously successful Revision-4 mechanical geometry with an explicit physical-mesh handedness gate.

## Physical handedness result

Housing source:

`keyball_trackball_case_25mm_type_c_right.stl`

Measured mesh:

- X bounds: **`[-9.6313896, +27.9633064]` mm**;
- ball position within housing: **left**;
- access opening: **-X / left / thumb side**;
- housing bulk: **+X / right / outward**;
- upper-rim -X vertices: `254`;
- upper-rim +X vertices: `1065`;
- -X/+X ratio: **0.238498**.

The gate fails if the ratio exceeds `0.5` or if the housing does not extend farther to +X than -X.

This directly prevents the Revision-5 filename-based handedness mistake.

## Qualified geometry

Ball center:

**`(15.5, -31.000147, 1.938015634)` mm**

Stack:

- switchplate bottom: `z=0`;
- switchplate top: `z=1.5 mm`;
- PCB top: `z=-3.5 mm`;
- PCB bottom: `z=-5.1 mm`.

Ball exposure above plate:

**12.938015634 mm**

PCB XY material distance from ball center:

**11.807963 mm**

## Mesh-level collision result

- sphere vs PCB: **0 mm³**
- housing vs PCB: **0 mm³**
- sphere vs relieved switchplate: **0 mm³**
- housing vs relieved switchplate: `5.34e-7 mm³`
- sphere vs relieved right case: **0 mm³**
- housing vs relieved right case: `3.41e-7 mm³`

The non-zero values are numerical boolean residue below the `0.01 mm³` gate.

All source meshes are watertight.

## Key reach

Nearest retained key centers:

- R33 / SW21: **34.196 mm**
- SW13: 34.659 mm
- SW15: 37.339 mm
- SW14: 40.157 mm
- SW16: 43.433 mm
- SW12: 44.413 mm

The digital model proves geometric access only. Subjective comfort remains a physical-mock-up question.

## Mounting and case pod

Qualified housing screw axes:

- `(21.712, -23.020147)` mm;
- `(21.712, -38.980147)` mm.

Case pod:

- wall: 1.5 mm;
- floor: 1.5 mm;
- boss outer radius: 3.0 mm;
- support at both M2 axes: **100%**;
- downward extension below stock case: **5.461946 mm**.

## Qualification evidence

Implementation head:

`c5023e227d6a766726e247d3e605949fe7b1d545`

Task 2E workflow:

- run ID: `36950226502`;
- conclusion: **success**.

The same head passes Tasks 2B, 2C, 2D, 3A, 3B, 3C and 3D.

## Remaining physical gate

Before production-final routing/fabrication, build the right-half mock-up and verify:

- thumb enters from the **left-side housing opening** naturally;
- R33/SW21 ↔ ball transition;
- ball seating, retention and motion;
- PMW optical stack;
- housing insertion/removal and screw access;
- seven-conductor cable bend and strain relief;
- case-pod desk contact/stability;
- actual M2 hardware.

Any failure that requires moving the ball or housing reopens Task 2.
