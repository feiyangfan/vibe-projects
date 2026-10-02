# Task 2 Revision 6 — Mesh-Verified Trackball Handedness

## Status

**PASS — COMPLETE.**

Revision 6 re-evaluates the design from the last mechanically qualified state before the mistaken Revision-5 handedness change.

The result is that the **Revision-4 geometry was physically oriented correctly**. Revision 6 restores that geometry and strengthens validation.

## Required right-thumb geometry

For the right hand:

```text
thumb -> left-side opening -> ball | housing / PMW / connector -> outside-right
                               -X                              +X
```

The ball must therefore sit toward the **left side of the housing**, with access from -X/left.

## Mesh-derived handedness

Housing source:

`Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl`

Task 2E now inspects the actual mesh and proves:

- local X bounds: `[-9.6313896, +27.9633064]` mm;
- -X extent from ball: `9.6313896 mm`;
- +X extent from ball: `27.9633064 mm`;
- ball position within housing: **left**;
- housing bulk side: **+X / right**;
- access opening: **-X / left**;
- upper-rim -X vertex count: `254`;
- upper-rim +X vertex count: `1065`;
- -X/+X rim ratio: **0.238498**, below the frozen maximum of `0.5`.

The validator no longer trusts `left` or `right` in the filename as the definition of handedness.

## Restored geometry

Revision 6 is geometrically equivalent to qualified Revision 4:

- ball XY: **`(15.5, -31.000147)` mm**;
- housing center from ball: **`(+9.165901, +0.000812)` mm**;
- housing screw midpoint from ball: **`(+6.212, 0)` mm**;
- breakout center from ball: **`(+19.212, 0)` mm**;
- board-side PMW 1x7: **`(0, -22.022143)` mm**, row on canonical Y;
- all 19 retained right MX keys preserved;
- all nine stock PCB holes preserved;
- R34 / SW22 / D22 remain removed;
- right encoder remains at the stock position.

Relative to invalid Revision 5, the ball moves `(-6.5, 0)` mm back to the qualified location.

## Qualification

Implementation head:

`c5023e227d6a766726e247d3e605949fe7b1d545`

Passing workflows on that head:

- Task 2B — run `36950226518`
- Task 2C — run `36950226630`
- Task 2D — run `36950226491`
- Task 2E — run `36950226502`
- Task 3A — run `36950226494`
- Task 3B — run `36950226458`
- Task 3C — run `36950226568`
- Task 3D — run `36950226512`

Task 3E may proceed from Revision 6. A physical right-half mock-up remains the ergonomic gate before production-final routing.
