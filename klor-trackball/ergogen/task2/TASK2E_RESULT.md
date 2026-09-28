# Task 2E Result — Full 3D Mechanical Integration

## Status

**PASS — COMPLETE.**

Task 2E proves the revision-4 trackball assembly in a common 3D frame using the real Type-C housing, a 25 mm sphere, the generated right PCB, stock Konrad switchplate and stock Konrad right case.

## Qualified geometry

Ball center:

`(15.5, -31.000147, 1.938015634)` mm

Stack:

- switchplate bottom: `z=0`;
- switchplate top: `z=1.5 mm`;
- Cherry MX plate-top to PCB-top: `5.0 mm`;
- PCB top: `z=-3.5 mm`;
- PCB bottom: `z=-5.1 mm`.

Ball exposure above plate top:

**12.938015634 mm**

Nearest retained key center:

- SW21: **34.196314 mm**.

## Mesh-level interference result

- 25 mm sphere vs PCB: **0 mm³**
- actual Type-C housing vs PCB: **0 mm³**
- sphere vs relieved switchplate: **0 mm³**
- housing vs relieved switchplate: `5.34e-7 mm³`
- sphere vs relieved right case: **0 mm³**
- housing vs relieved right case: `3.41e-7 mm³`

The non-zero values are numerical boolean residue below the `0.01 mm³` qualification tolerance.

All source meshes are watertight.

## Mechanical changes proven necessary

Task 2E disproved the revision-3 rigid PMW peninsula:

- revision-3 housing/PCB collision: approximately **158.111 mm³**;
- a Z-only workaround required approximately **24 mm** of ball exposure and was rejected.

Revision 4 therefore:

- moves the ball only `(-1,-3) mm` from revision 3;
- derives the PCB cavity from the actual housing/sphere clearance;
- preserves all 19 retained right keys and all nine PCB holes;
- retains the Kivipallur connector on the +X/right side of the ball;
- moves the keyboard-side 1x7 header to reclaimed SW22 PCB area;
- uses a short seven-conductor cable between the board and Kivipallur breakout.

## Switchplate and right case

The relieved switchplate is clearance-only around the housing.

The real housing relief removes the old plate support at the two native housing screw axes, so the right case gains a local downward pod and two bottom M2 mounting bosses.

Qualified pod:

- wall: 1.5 mm;
- floor: 1.5 mm;
- boss outer radius: 3.0 mm;
- both boss support checks: **100%**;
- downward extension below stock case: **5.461946 mm**.

This pod depth is a known physical/industrial-design tradeoff. It should be checked with a printed mock-up for desk contact and subjective comfort.

## Qualification evidence

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Workflow:

- `KLOR Task 2E - 3D mechanical integration`
- run ID: `36376432664`
- conclusion: **success**

Artifact:

- `klor-task2e-3d-mechanical`
- artifact ID: `10950704578`
- SHA-256: `2d208bd05d018efb2099c31cfbfd0417193509a0986bcfd9cfa8c683f952fca9`

Contents:

- `task2e_konrad_switchplate_trackball.stl`
- `task2e_konrad_case_right_trackball.stl`
- `task2e_trackball_assembly.glb`
- `task2e_mechanical_result.json`

The same qualification head passed Tasks 2B, 2C revision 4, 2D revision 4, 3A, 3B, 3C and 3D revision 4.

## Conclusion

The revision-4 design is mechanically self-consistent in the declared source-aligned 3D frame: the actual housing and ball can coexist with the generated PCB and the generated plate/case modifications.

A physical print remains required for final subjective ergonomics and real-world desk-clearance validation.
