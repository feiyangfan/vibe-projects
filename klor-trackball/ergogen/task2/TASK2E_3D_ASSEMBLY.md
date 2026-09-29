# Task 2E — 3D Trackball Assembly Validation

## Status

**IN PROGRESS**

Task 2 revision 3 fixed the right-PCB cavity, but the complete physical assembly is not yet proven.

## Finding carried forward from revision 3

The revision-3 PCB is a credible trackball substrate:

- the 25 mm ball center is frozen at canonical `(16.5, -28.000147)`;
- the actual Type-C housing STL has an XY bounding-box center at approximately `(+9.166, 0)` relative to its ball frame, matching the frozen Ergogen housing-center relationship;
- the regenerated PCB's nearest actual Edge.Cuts is `12.323043 mm` from the ball center;
- the retained key/housing conservative limiting gap is SW16 at approximately `2.580294 mm`;
- the PMW header, R33/SW21 and MH8 remain outside the revision-3 cavity.

However, those checks are two-dimensional or PCB-local. They do **not** prove the full keyboard assembly.

The current switchplate model still exposes only the old SW22/service opening rather than a complete Type-C housing/ball relief, and the exact housing Z placement relative to the PCB/plate/case has not been regression-checked.

Therefore:

> **The revision-3 PCB is accepted as the current PCB geometry, but the complete trackball assembly is not declared installable until Task 2E passes.**

## Objective

Place these real artifacts in one reproducible coordinate system:

1. generated revision-3 right PCB;
2. actual `keyball_trackball_case_25mm_type_c_right.stl`;
3. a 25 mm sphere at the frozen ball center;
4. stock Konrad 3DP switchplate STL;
5. stock Konrad right case STL.

Then:

- derive and freeze the stock switchplate/case -> canonical transform;
- derive the physical Z stack;
- cut only the local plate/case relief required by the Type-C housing and ball;
- preserve retained switch/mounting geometry;
- run mesh-level collision/interference checks;
- emit transformed/cut STL artifacts and a machine-readable clearance report.

## Pass criteria

Task 2E passes only when all are true:

- the housing and ball use the frozen Task-2 XY location and connector-right orientation;
- the housing/ball do not intersect the PCB;
- the housing/ball do not intersect the revised switchplate;
- the housing/ball do not intersect the revised right case except at intentional mounting/contact interfaces;
- the ball has a continuous exposed operating surface above the plate/case opening;
- the two housing mounting axes remain physically realizable;
- retained R32/R33, encoder, stock PCB holes and case/switchplate structural axes are not cut;
- remaining material around the trackball relief meets an explicit minimum wall/ligament rule;
- transformed/cut meshes regenerate deterministically.

## Ergonomics scope

Task 2E can validate geometric reach proxies and physical access, but it cannot prove subjective comfort for every hand.

The frozen ball center is about:

- `32.5 mm` from SW13;
- `34.4 mm` from SW15;
- `34.8 mm` from retained SW21/R33;
- `41.5 mm` from SW16.

This is physically plausible for a thumb cluster, but final ergonomic acceptance still requires at least a printed/mock assembly or user fit check after the 3D interference gate passes.
