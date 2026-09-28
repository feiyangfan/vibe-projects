# Task 2E — 3D Trackball Mechanical Integration

## Status

**IN PROGRESS**

## Why this task exists

Task 2 revision 3 corrected the right-PCB trackball cavity. The generated PCB now has an open-edge cavity with 12.323043 mm minimum XY distance from the ball center to actual Edge.Cuts.

That is necessary, but not sufficient to prove a usable assembly.

A 25 mm sphere has a 12.5 mm radius, so ball/PCB clearance depends on the **vertical separation** between the ball center and PCB. More importantly, the current switchplate still contains only the old SW22/service opening; it has not yet been relieved around the real Type-C housing.

Therefore the complete assembly was not yet proven installable.

## Existing facts retained

- ball canonical XY: `(16.5, -28.000147)`;
- Type-C housing local XY is ball-centered;
- the real housing STL XY bounding-box center is approximately `(+9.16596, -0.01121)`, matching the Ergogen housing-center relation `(+9.165901, +0.000812)`;
- connector/breakout remain on +X / right side of the ball;
- PCB cavity topology and PMW peninsula remain Task-2 revision 3;
- retained electrical architecture is unchanged.

## Common coordinate system

### XY

Canonical origin remains stock SW13.

- canonical +X = source KiCad +X;
- canonical +Y = reflected source KiCad Y;
- stock switchplate native XY uses the already source-validated Task-2B rigid transform;
- stock right-case XY is converted from its source CAD/KiCad global frame into the same SW13-centered canonical frame;
- the Type-C housing local origin is the 25 mm ball center and is translated to the frozen canonical ball XY.

### Z

Task 2B only froze 2D geometry. Task 2E therefore makes the stack datums explicit.

- switchplate bottom = `z=0`;
- switchplate thickness is read from the actual STL (nominally 1.5 mm);
- right-case Z is translated so its source top surface aligns with the switchplate top;
- PCB thickness = 1.6 mm;
- PCB top = `z=-5.0 mm`.

The PCB-top value is an explicit MX-stack engineering datum, not a previously source-validated Task-2 value. The Task-2E result must keep this limitation visible.

## Ball/housing Z solve

Task 2E does not pick ball height by appearance.

It starts from the minimum ball center Z that provides at least **0.5 mm Euclidean clearance** between the 25 mm sphere and the generated revision-3 PCB solid.

It then raises the housing/ball in 0.25 mm increments only if the **actual housing STL** still intersects the PCB.

The selected height must also leave a useful exposed ball cap above the switchplate.

## Plate and case relief

The trackball-specific relief is generated from the actual Type-C housing mesh, not from the old 37.6 x 30 mm reference rectangle alone.

Manufacturing keepout:

- housing XY clearance: 0.5 mm;
- housing Z clearance: 0.3 mm;
- ball radial clearance: 0.3 mm.

The clearance-expanded housing and ball keepouts are boolean-subtracted from:

1. the real Konrad switchplate STL;
2. the real Konrad right-case STL.

Housing mounting axes are then checked so the relief does not silently remove all usable plate support around the intended screw locations.

## Completion gate

Task 2E passes only when:

- all five real/generated artifacts share one declared coordinate frame;
- the sphere does not intersect the generated PCB;
- the actual Type-C housing does not intersect the generated PCB;
- relieved switchplate has no intersection with the actual housing or sphere;
- relieved right case has no intersection with the actual housing or sphere;
- switchplate remains mechanically connected;
- both housing mounting axes retain usable surrounding plate material or an explicit replacement mount is designed;
- generated relieved plate/case STLs and a machine-readable result are produced as CI artifacts;
- the selected ball height and exposed cap are recorded rather than inferred visually.

## Ergonomics boundary

Task 2E can prove geometric access and quantify ball exposure/key distances. It cannot prove subjective comfort for every hand size. A printed mock-up remains the final ergonomic validation.
