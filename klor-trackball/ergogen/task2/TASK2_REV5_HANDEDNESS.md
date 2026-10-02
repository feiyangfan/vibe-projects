# Task 2 Revision 5 — INVALID Housing-Handedness Interpretation

## Status

**INVALID / SUPERSEDED BY REVISION 6.**

Revision 5 was created after incorrectly interpreting the checked-in STL filenames as physical handedness labels.

The assumption was:

- `type_c_right.stl` = opening on the right;
- `type_c_left.stl` = opening on the left.

That assumption is false for the physical geometry needed by this keyboard.

## What the mesh actually says

The ball-centered STL geometry is the authority.

`keyball_trackball_case_25mm_type_c_right.stl`:

- local X bounds are approximately `[-9.631, +27.963]` mm;
- the housing extends much farther to +X than -X, so the **ball sits toward the left side of the housing**;
- a direct upper-rim mesh probe measures a -X/+X vertex ratio of about `0.238`, identifying the **access opening on -X / left**;
- the housing bulk and connector-side structure extend toward +X / right.

That is exactly the required right-thumb orientation.

By contrast, `type_c_left.stl` is the X-mirrored counterpart: its housing bulk is on -X and its access opening is on +X. Revision 5 therefore moved the ball outward to solve clearances for the **wrong physical orientation**.

## Consequence

The Revision-5 geometry at `(22.0, -31.000147)` and its rotated board-side PMW header at `(18.5, -14.5)` are not the product baseline.

Revision 6 restores the previously qualified Revision-4 geometry and adds mesh-derived handedness regression checks so this error cannot recur.

Do not use Revision-5 result files or coordinates as current design authority.
