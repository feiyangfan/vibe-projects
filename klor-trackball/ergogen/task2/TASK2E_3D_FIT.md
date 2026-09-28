# Task 2E — Full 3D Trackball Assembly Fit

## Status

**IN PROGRESS — revision-3 PCB accepted as the starting substrate; full assembly not yet qualified.**

## Why this task exists

Task 2 revision 3 corrected the PCB cavity and proved that the generated right PCB provides a KLORBall-35-style open-edge clearance around the 25 mm ball.

That is not sufficient to claim the trackball can be installed and used.

The complete assembly also contains:

- the actual Keyball 25 mm Type-C housing;
- the 25 mm ball;
- the switchplate;
- the right case;
- a physical retention method for the housing.

The revision-3 plate model still contains only the historical SW22 + service opening. It has not been cut for the real Type-C housing.

## Findings before Task 2E

### Type-C housing

Checked-in source:

`Keyball 25mm Trackball Case Type C - 6719828/files/keyball_trackball_case_25mm_type_c_right.stl`

Measured mesh envelope:

- X: -9.631390 .. +27.963306 mm;
- Y: -14.998107 .. +14.975688 mm;
- Z: -18.000000 .. +13.200000 mm;
- XY size: 37.594696 x 29.973795 mm;
- total height: 31.200000 mm.

The STL is already centered on the ball axis: the 25 mm ball center is the housing-local origin.

The broad planar housing base is at local **Z = -18.0 mm**.

Frozen Type-C screw axes, housing-local / ball-relative:

- screw 1: `(+6.212, +7.980)`;
- screw 2: `(+6.212, -7.980)`.

### Revision-3 PCB

Ball center remains:

`(16.5, -28.000147)` in the canonical SW13 frame.

The PCB cavity contains both Type-C screw axes, so those screws cannot be retained by PCB material.

The revision-3 generated PCB still passes its 2D mechanical gate:

- minimum explicit cavity distance from ball center: 10.934113 mm;
- nearest generated Edge.Cuts: 12.323043 mm.

Those values remain useful PCB checks, but they are not a 3D assembly proof.

### Stock switchplate

Checked-in source:

`klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl`

Mesh thickness: 1.5 mm.

Eight structural mounting holes solve the canonical-to-STL XY transform without scaling:

```text
x_plate ~= x_canonical + 59.421 mm
y_plate ~= -y_canonical + 57.623 mm
```

Residuals are on the order of hundredths of a millimeter.

At the two Type-C screw axes the stock plate cross-section is already open. Therefore the stock plate cannot be used as the housing screw carrier without adding new bridge/tab geometry.

The ball center itself lies in stock plate material, so a trackball-specific plate relief is mandatory.

### Stock right case

Checked-in source:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

The same eight structural-hole distance fingerprints solve:

```text
x_case ~= x_canonical + 140.005 mm
y_case ~= -y_canonical + 113.573 mm
```

The case has a broad bottom at Z=-4.8 mm, an inner floor around Z=-3.0 mm, and a top rim at Z=+8.8 mm.

At the ball and both Type-C screw axes, case material exists in the floor region (approximately Z=-4.8 .. -3.0) and the volume above roughly Z=-2.5 is open.

This gives a mechanically coherent retention path: add two case-supported bosses at the Type-C screw axes rather than relying on the absent PCB/plate material.

## Task-2E assembly strategy

Task 2E will use the **case as the structural carrier** for the Type-C housing.

Planned retained interface:

- two M2-class bosses grow from the existing case floor at the frozen Type-C screw axes;
- the housing base is supported above the case floor at the qualified assembly Z;
- the PCB remains open around the housing;
- the switchplate is subtractively relieved for the housing + ball envelope;
- the case is subtractively relieved only where the positioned housing/ball intersects existing case material;
- the existing case floor and structural mount system remain intact outside the local trackball interface.

The final boss/hardware dimensions and Z datum are not frozen until the full mesh interference check passes.

## Qualification requirement

Task 2E is not complete until a clean checkout can reproduce:

1. the common coordinate transforms;
2. the positioned housing + 25 mm sphere + PCB + switchplate + case scene;
3. the modified switchplate STL;
4. the modified case STL with housing retention;
5. a machine-readable clearance report proving no volumetric interference over the qualified Z tolerance window.

A visual render alone is not sufficient.
