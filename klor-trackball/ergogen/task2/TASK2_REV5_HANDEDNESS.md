# Task 2 Revision 5 — Trackball Housing Handedness Correction

## Status

**IN PROGRESS — revision 4 invalidated by physical handedness audit.**

## Problem

Revision 4 was mechanically qualified with:

`Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl`

while the design contract independently required the Kivipallur/Type-C connector to face the keyboard's **right / +X / outward** side.

For the checked-in Type-C housing pair, the `right.stl` physical part has the connector on the **left** side and the ball-holder opening on the **right**. On the right keyboard half this reverses the intended service orientation: the opening faces outward and the connector faces inward.

The matching `left.stl` is the X-mirrored counterpart and gives the desired right-half orientation:

```text
thumb / retained keys <- ball opening | ball | housing / connector -> outside edge
```

Therefore revision 4 proved collision-free geometry for the wrong handed housing. Its fit result is not sufficient to authorize Task 3E or routing.

## Evidence

The two checked-in STL meshes are mirrored counterparts in X:

- `right.stl` X bounds: approximately `[-9.631, +27.963]` mm;
- `left.stl` X bounds: approximately `[-27.963, +9.631]` mm.

A direct vertex audit shows approximately 99.9% mirrored vertex correspondence after X reflection.

The implementation error is explicit in `scripts/validate_task2e.py`, which hard-coded `...type_c_right.stl` while the Task-2/Task-3 contracts described the connector as `positive_canonical_x`.

## Revision-5 objective

Re-run the full mechanical qualification with the correctly handed housing and find the smallest valid geometry change.

Required gates:

1. use `keyball_trackball_case_25mm_type_c_left.stl` for the right keyboard half;
2. opening faces inward/left toward the thumb cluster;
3. connector faces outward/right (+X);
4. preserve R32/R33 and all 19 retained right keys if possible;
5. preserve all nine PCB mounting holes if possible;
6. derive the PCB cavity from the actual correctly handed housing section plus ball clearance;
7. re-run switchplate/case relief and housing-boss generation;
8. re-run Task 2C, 2D, 2E and Task 3D regression;
9. do not start Task 3E until the new revision passes.

## Change control

Revision 4 remains useful historical evidence, but its mechanical qualification is superseded because it validated the wrong physical housing handedness.

Any new ball XY, cavity, board-header location, case pod, or housing mounting geometry discovered by the revision-5 search must be frozen as a new Task-2 revision and propagated into Task 3D before electrical pair freeze.
