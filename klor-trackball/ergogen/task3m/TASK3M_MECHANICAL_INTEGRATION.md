# Task 3M — Trackball Mechanical Integration

## Status

**IN PROGRESS — full 3D fit uncovered and is correcting an MH7 conflict.**

## Why this task exists

Task 2 revision 3 fixed the right-PCB cavity and proved that the generated PCB leaves an open KLORBall-35-style trackball region. That is necessary but not sufficient for a manufacturable keyboard.

A PCB-plane clearance result does **not** prove that the complete stack can be assembled. The actual Type-C housing, 25 mm ball, switchplate, and case must share one 3D frame and be checked together.

## Findings carried forward

Qualified PCB facts:

- ball center after Task-3M fit correction: `(16.5, -31.500147)` mm in the canonical SW13 frame;
- PMW connector remains on the +X/right side of the ball;
- nearest production PCB Edge.Cuts: **12.323043 mm** from the ball center;
- R32/R33 and the right encoder remain;
- R34/SW22/D22 remain removed.

Important limitation of the previous result:

- the current switchplate model still uses the old SW22 + 2 x 22 mm service opening;
- therefore the PCB may be valid while the complete trackball housing cannot yet pass through the plate/case.

## Source geometry

This task uses the checked-in production source assets directly:

- `Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl`;
- `klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl`;
- `klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`;
- generated `task3d_right_production.kicad_pcb`.

The Type-C housing STL is approximately **37.595 x 29.974 x 31.200 mm**. Its XY center is `(+9.16596, -0.01121)` from the ball origin, matching the frozen Ergogen housing offset `(+9.165901, +0.000812)` to transform tolerance.

The stock Konrad switchplate STL is approximately **150.271 x 104.791 x 1.500 mm**. Its XY envelope matches the canonical plate envelope, and shape matching proves that the STL Y axis is mirrored relative to the Ergogen frame.

Frozen plate registration:

```text
x_canonical = x_stl - 59.425799794
y_canonical = -y_stl + 57.733750114
```

## Z-stack contract

World Z is defined with **PCB top = 0 mm**.

The Type-C housing has a large planar mounting face at local `z = -18 mm`. Task 3M places that face at PCB top, giving:

- housing local `z=-18` -> world `z=0`;
- ball center -> world `z=18` mm;
- 25 mm ball bottom -> world `z=5.5` mm.

The stock plate is 1.5 mm thick. For MX geometry, plate top is modeled at 5.0 mm above PCB top, so:

- plate bottom = `z=3.5` mm;
- plate top = `z=5.0` mm.

That gives only **0.5 mm nominal vertical ball-to-uncut-plate clearance**. Revision 3 must therefore not rely on the vertical gap alone: the modified plate gets a full ball aperture plus housing relief.

The stock right-case STL is registered to the plate by its CAD-envelope center and translated in Z so the stock case top rim is at the same `z=5.0` plate-top plane.

## Relief strategy

The actual housing mesh, not its rectangular bounding box, defines the lower housing profile.

At the plate/case stack (`housing local z=-14.5..-13.0` for the plate and `-18..-13.0` for the case), the conservative convex profile is approximately:

```text
[-7.844, +1.723]
[-7.077, -2.706]
[-5.476, -5.972]
[-2.384, -8.515]
[+5.533,-10.899]
[+15.015,-12.975]
[+21.353,-12.878]
[+23.434,-12.208]
[+25.620,-10.657]
[+26.892, -9.000]
[+27.763, -6.780]
[+27.963, +5.000]
[+27.691, +7.071]
[+26.892, +9.000]
[+25.620,+10.657]
[+23.963,+11.928]
[+21.743,+12.799]
[+14.769,+12.939]
[+5.533,+10.899]
[-2.514, +8.424]
[-5.370, +7.170]
[-6.738, +5.727]
```

Coordinates are ball-relative.

The production relief is the union of:

1. the actual lower-housing profile with manufacturing clearance;
2. a circular ball aperture larger than the 12.5 mm ball radius.

Initial frozen margins for validation:

- plate housing relief: **0.75 mm**;
- case housing relief: **1.00 mm**;
- ball aperture radius: **13.25 mm** (0.75 mm radial margin).

## Completion gate

Task 3M is complete only when a clean checkout:

1. regenerates the Task-3D right PCB;
2. registers the actual housing, ball, PCB, stock switchplate and stock right case into one world frame;
3. produces cut right switchplate and case meshes;
4. proves no unintended housing/ball intersection with the modified plate/case;
5. proves the housing does not penetrate the PCB volume below its mounting plane;
6. preserves all retained right-key apertures and stock structural axes outside the local relief;
7. exports a common-frame 3D assembly artifact and a machine-readable fit report.

This task is a prerequisite to treating the trackball assembly as mechanically installable. Task 3E remains the electrical pair freeze and does not substitute for Task 3M.


## Revision-4 placement correction

The first common-frame boolean run found a genuine revision-3 conflict: the actual lower Type-C housing profile was only **0.542 mm** from MH7 center. That cannot preserve a 3.2 mm M3 drill plus case-relief allowance.

Task 2 is therefore reopened as revision 4 for one localized change:

- move the complete trackball assembly **3.5 mm downward in canonical Y**;
- new ball center: `(16.5, -31.500147)`;
- keep X, connector handedness, keys, encoder, MCU, TRRS and all structural axes unchanged;
- lengthen the PMW support tongue so it still joins the unchanged stock PCB edge.

At the revision-4 position the actual housing projection is approximately **3.82 mm** from MH7 center, providing room for the 1.6 mm M3 radius, 1.0 mm case relief, and at least 0.5 mm residual structural margin.

This correction was discovered by the 3D gate and is intentionally not waived.


### Revision-4 service corridor

Moving the trackball assembly downward also moves the breakout center downward. The previous 2 x 22 mm slot then stops short of the unchanged stock lower PCB edge. Revision 4 therefore lengthens only the slot's Y dimension to **2 x 26 mm**. The slot width, breakout X, PMW header relationship, and connector handedness are unchanged. The longer slot still retains comfortable clearance to MH8.


## Qualification note

The common-frame mechanical gate is intentionally iterative: any discovered
collision must be corrected in geometry or relief rather than waived. The final
Task 3M status is set to PASS only after the exported modified switchplate,
case, PCB, housing and ball assembly passes the machine interference checks.
