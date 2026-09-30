# Task 2 Revision 5 — Trackball Housing Handedness Correction

## Status

**PASS — COMPLETE. Revision 5 supersedes revision 4.**

## Problem found

Revision 4 qualified `keyball_trackball_case_25mm_type_c_right.stl` while separately assuming the physical housing/Kivipallur connector faced +X/right.

That assumption was wrong for the checked-in part. On the right keyboard half:

- `right.stl` puts the connector inward/left and the ball opening outward/right;
- `left.stl` is its X-mirrored counterpart and gives the required orientation.

Revision 4 was therefore collision-free for the **wrong physical handedness**.

## Correct Rev-5 orientation

The right keyboard half now uses:

`Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_left.stl`

Required physical orientation:

```text
thumb / retained keys <- ball opening | ball | housing / connector -> outside edge
                         -X                             +X
```

Mesh evidence:

- source `right.stl` X bounds: about `[-9.631, +27.963]` mm;
- source `left.stl` X bounds: about `[-27.963, +9.631]` mm;
- the meshes are X-mirrored counterparts to transform tolerance.

A regression guard now rejects the wrong source handedness.

## Qualified Rev-5 placement

Canonical ball center:

**`(22.0, -31.000147)` mm**

Common-frame Z:

**`1.938015634 mm`**

Ball exposure above the 1.5 mm plate:

**12.938015634 mm**

Relative to Rev 4, the ball moves **(+6.5, 0) mm**. The outward movement is required to keep the correctly handed housing clear of retained keys while retaining the conservative housing/key margin.

Preserved:

- all 19 right MX keys;
- R32 / SW20;
- R33 / SW21;
- right encoder;
- all nine stock PCB holes;
- MCU and TRRS datums.

The conservative rectangular housing-to-retained-key gap is approximately **2.683 mm**. The nearest retained key center overall is SW15 at approximately **33.779 mm**. R33/SW21 is approximately **40.608 mm** center-to-center from the ball, so physical thumb-reach validation remains mandatory.

## Housing and mounting datums

- housing center from ball: `(-9.165901, +0.000812)` mm;
- native screw midpoint from ball: `(-6.212, 0)` mm;
- screw Y offsets: `+7.98 / -7.98` mm;
- qualified screw axes: approximately `(15.788, -23.020147)` and `(15.788, -38.980147)` mm.

The plate relief removes useful support at those axes, so the housing remains mounted by the local right-case pod with two bottom M2 bosses.

## PMW connector distinction

The **housing/Kivipallur connector** remains outward on +X.

The **keyboard-side 1x7 header** is a separate cabled connector at:

**`(18.5, -14.5)` mm**

It is rotated **90°**, with its row on canonical X:

- pin 1 / CS at +X;
- pin 7 / GND at -X.

The same seven signals and breakout-pin-`N` to keyboard-pin-`8-N` cable mapping are retained.

## Qualification

Implementation qualification head:

`0b704c8ff85c6b641b796813f49e78124d8e21ec`

Passing workflows on that head:

- Task 2B: `36697008269`
- Task 2C: `36697008095`
- Task 2D: `36697008291`
- Task 2E: `36697008540`
- Task 3A: `36697008121`
- Task 3B: `36697008068`
- Task 3C: `36697008184`
- Task 3D: `36697008138`

Revision 4 remains historical evidence only.
