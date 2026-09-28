# Task 2E — 3D Trackball Mechanical Integration

## Status

**PASS — COMPLETE.**

Task 2E closes the gap between a plausible 2D PCB cavity and an installable 3D trackball assembly.

The qualification places the following artifacts in one declared coordinate frame and performs mesh-level boolean/interference checks:

- generated revision-4 right PCB;
- actual Keyball 25 mm Type-C right housing STL;
- a 25 mm sphere;
- stock Konrad switchplate STL;
- stock Konrad right-case STL.

## What Task 2E found

### Revision 3 was not physically valid

Revision 3 cleared the nominal ball in 2D, but the **actual Type-C housing** intersected the generated PCB by approximately **158.111 mm³** at a useful ball height.

Trying to solve that collision only by raising the housing did not work ergonomically: the housing cleared only with approximately **24 mm of the 25 mm ball exposed above the plate**.

That invalidated the revision-3 rigid PMW peninsula as a production mechanical interface.

### Minimum revision-4 correction

A local search against the actual housing, all 19 retained keys, and all nine stock PCB holes found a minimum nearby clean placement:

- revision-3 ball XY: `(16.5, -28.000147)`;
- revision-4 ball XY: **`(15.5, -31.000147)`**;
- shift: **`(-1, -3) mm`**;
- shift norm: approximately **3.162 mm**.

All 19 right keys and all nine stock PCB holes remain.

The PCB cavity is now derived from the real housing section through the PCB slab plus sphere/manufacturing clearance, rather than from a nominal rectangle or a KLORBall-35-inspired 2D shape alone.

## PMW mechanical interface

The Kivipallur breakout/connector remains on the **+X / right side of the ball**.

The old rigid keyboard-PCB PMW peninsula occupied the real housing volume and was therefore removed.

Revision 4 uses:

- Kivipallur connector on the right side of the ball;
- keyboard-side 1x7 header at canonical **`(0, -22.022143)`**, in reclaimed SW22 PCB area;
- a short seven-conductor cable between them;
- unchanged signal contract: CS, MISO, MOSI, SCK, NC/MOTION, 3V3, GND;
- unchanged mating rule: breakout pin N maps to keyboard pin `8-N`.

## Common coordinate system

### XY

Canonical origin remains stock SW13.

- canonical +X = source KiCad +X;
- canonical +Y = reflected source KiCad Y;
- switchplate uses the existing Task-2B source-validated rigid transform;
- right-case XY is converted from source CAD/KiCad coordinates to the same SW13-centered frame;
- housing local XY origin is the ball center.

The real housing STL's XY bounding-box center is approximately `(+9.16596, -0.01121)`, consistent with the frozen housing-center relation `(+9.165901, +0.000812)`.

### Z

- switchplate bottom: `z=0`;
- actual switchplate top: `z=1.5 mm`;
- Cherry MX plate-top to PCB-top stack datum: **5.0 mm**;
- PCB top: **`z=-3.5 mm`**;
- PCB thickness: **1.6 mm**;
- PCB bottom: **`z=-5.1 mm`**;
- stock right-case top aligned to switchplate top.

The 5.0 mm plate-top-to-PCB-top dimension replaces the earlier provisional `PCB top = -5.0 mm` assumption.

## Qualified ball installation

The solver selects the lowest ball Z that preserves at least 0.5 mm Euclidean ball-to-PCB clearance while the actual housing remains collision-free.

Qualified ball center:

**`(15.5, -31.000147, 1.938015634) mm`**

Results:

- ball radius: 12.5 mm;
- ball exposure above plate top: **12.938 mm**;
- generated PCB XY material distance from ball center: **11.808 mm**;
- sphere vs PCB intersection: **0 mm³**;
- housing vs PCB intersection: **0 mm³**.

The exposed cap is therefore approximately half the ball diameter rather than the rejected ~24 mm exposure from the revision-3 Z-only workaround.

## Switchplate and case

The real housing and sphere keepouts are subtracted from the stock Konrad switchplate and right case.

The required plate relief consumes the old plate support around the housing's two native mounting axes. Consequently, Task 2E does **not** claim those screws mount through the plate.

Instead the right case gains a local downward trackball pod:

- wall thickness: 1.5 mm;
- floor thickness: 1.5 mm;
- overlap into stock case: 2.0 mm;
- two native M2-axis bottom bosses;
- boss outer radius: 3.0 mm;
- M2 hole diameter: 2.1 mm;
- boss support check: **100% at both axes**.

The pod extends **5.462 mm below the original stock-case bottom**. This is an intentional modeled enclosure, not an unresolved collision.

## Final interference result

At the qualified geometry:

- sphere vs PCB: **0 mm³**;
- housing vs PCB: **0 mm³**;
- sphere vs relieved switchplate: **0 mm³**;
- housing vs relieved switchplate: approximately `5.34e-7 mm³`;
- sphere vs relieved case: **0 mm³**;
- housing vs relieved case: approximately `3.41e-7 mm³`.

The non-zero housing values are numerical boolean residue far below the 0.01 mm³ qualification tolerance.

All source meshes used by the gate are watertight.

## Ergonomic geometry

Nearest retained key-center distances from the ball center:

- SW21: **34.196 mm**;
- SW13: 34.659 mm;
- SW15: 37.339 mm;
- SW14: 40.157 mm;
- SW16: 43.433 mm;
- SW12: 44.413 mm.

This is a mechanically plausible thumb position and gives a useful exposed ball cap. It is **not** proof of subjective comfort for every hand size.

The 5.462 mm local pod depth can also affect flat-on-desk stance. A printed physical mock-up remains the final ergonomic/desk-clearance validation.

## Qualification

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Passing workflow:

- `KLOR Task 2E - 3D mechanical integration`
- run ID: `36376432664`
- conclusion: **success**

Artifact:

- `klor-task2e-3d-mechanical`
- artifact ID: `10950704578`
- SHA-256: `2d208bd05d018efb2099c31cfbfd0417193509a0986bcfd9cfa8c683f952fca9`

Artifact contents:

- `task2e_konrad_switchplate_trackball.stl`
- `task2e_konrad_case_right_trackball.stl`
- `task2e_trackball_assembly.glb`
- `task2e_mechanical_result.json`

The same qualification head also passed Tasks 2B, 2C, 2D, 3A, 3B, 3C and 3D.
