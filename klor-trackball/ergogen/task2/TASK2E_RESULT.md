# Task 2E Result — Full 3D Mechanical Integration Revision 5

## Status

**PASS — COMPLETE.**

Revision 5 corrects the housing-handedness error discovered after revision 4 and re-qualifies the complete right-side mechanical stack.

## Correct physical housing

Right keyboard half source:

`keyball_trackball_case_25mm_type_c_left.stl`

This is intentional. For the checked-in mirrored housing pair it gives:

- ball-holder opening toward **-X / inward / thumb side**;
- housing/Kivipallur connector toward **+X / outward**.

Revision 4 used the opposite source and is superseded.

## Qualified geometry

Ball center:

**`(22.0, -31.000147, 1.938015634)` mm**

Stack:

- switchplate bottom: `z=0`;
- switchplate top: `z=1.5 mm`;
- PCB top: `z=-3.5 mm`;
- PCB bottom: `z=-5.1 mm`.

Ball exposure above plate:

**12.938015634 mm**

PCB XY material distance from ball center:

**14.211815 mm**

The Rev-4-qualified Z was deliberately retained so correcting handedness did not silently change ball exposure.

## Mesh-level result

- sphere vs PCB: **0 mm³**
- correctly handed housing vs PCB: **0 mm³**
- sphere vs relieved switchplate: **0 mm³**
- housing vs relieved switchplate: `6.47e-8 mm³`
- sphere vs relieved right case: **0 mm³**
- housing vs relieved right case: `4.40e-7 mm³`

The non-zero values are numerical boolean residue far below the `0.01 mm³` gate.

All source meshes are watertight.

## Placement and ergonomic geometry

The correctly handed housing forces the ball farther outward than revision 4.

- Rev-4 ball: `(15.5, -31.000147)`
- Rev-5 ball: `(22.0, -31.000147)`
- delta: **(+6.5, 0) mm**
- conservative rectangular housing/key gap: about **2.683 mm**

Nearest retained key centers:

- SW15: **33.779 mm**
- SW16: 37.438 mm
- SW13: 38.013 mm
- SW14: 40.109 mm
- R33 / SW21: **40.608 mm**
- SW12: 49.633 mm

This is digitally feasible, but the increased R33-to-ball reach is a real ergonomic risk and must be checked physically.

## PMW interface

The housing/Kivipallur connector remains outward on +X.

Keyboard-side cabled 1x7:

- center: **`(18.5, -14.5)`**;
- rotation: **90°**;
- row axis: X;
- pin 1 / CS: +X end;
- pin 7 / GND: -X end.

A short seven-conductor cable connects the board header to the breakout.

## Case pod and mounting

Qualified screw axes:

- `(15.788, -23.020147)` mm;
- `(15.788, -38.980147)` mm.

Case pod:

- wall: 1.5 mm;
- floor: 1.5 mm;
- boss outer radius: 3.0 mm;
- both boss support checks: **100%**;
- downward extension below stock case: **5.461946 mm**.

## Qualification evidence

Implementation qualification head:

`0b704c8ff85c6b641b796813f49e78124d8e21ec`

Task 2E workflow:

- run ID: `36697008540`;
- conclusion: **success**.

Artifact:

- name: `klor-task2e-3d-mechanical`;
- artifact ID: `11088143644`;
- SHA-256: `b2aba7e45e331cbc72ff3e73f977d35987dfe4a288c9bf896b27b8bb74859817`.

The same implementation head passes Tasks 2B, 2C, 2D, 3A, 3B, 3C and 3D.

## Remaining physical gate

Before Task 4 routing is treated as production-final, build a right-half mock-up and verify:

- natural thumb reach to the farther-out Rev-5 ball;
- transition between R33/SW21 and the ball;
- ball retention and free motion;
- PMW3360 optical stack;
- housing insertion/removal and screw access;
- seven-conductor cable bend/strain behavior;
- case-pod desk contact and keyboard stability;
- actual M2 fastener stack.

If this reveals a geometry problem, reopen Task 2 before routing.
