# Task 2A — Minimal-Change Trackball Integration Study

## Status

**COMPLETE — implementation baseline selected for Task 2B/2C**

This study answers one question before the full Ergogen reconstruction begins:

> What is the smallest geometric and electrical change set required to add the 25 mm PMW3360 trackball to the KLOR 1.4 MX / Konrad right half?

The goal is not to preserve the retired KiCad implementation. The goal is to preserve as much **stock KLOR product geometry** as possible while making the trackball interface reproducible.

---

## Conclusion

For the stated **minimal-change** objective, the implementation baseline should be:

- remove **R34 / SW22 / D22** only;
- retain **R32 / SW20**;
- retain **R33 / SW21**;
- retain the **right encoder** in its stock location;
- use the previously source-validated Type-C housing placement as the initial canonical trackball placement;
- preserve all stock structural mounting axes;
- preserve the stock PCB outline everywhere except the breakout/service notch if possible;
- preserve the stock switchplate perimeter and structural holes;
- modify only the local right-case shell around the housing.

The right encoder is retained not because it is intrinsically required, but because removing it provides no useful space for the minimal-change placement. The historical audit measured approximately **27.77 mm** conservative housing-to-encoder clearance.

Removing R33 is a legitimate alternative if we later decide that a substantially more inward trackball position is worth losing another thumb key. It is not the minimum-change solution.

---

## Evidence base

This study reuses verified source-geometry evidence from the retired implementation only where that evidence remains relevant:

- stock KLOR 1.4 PCB;
- stock Konrad switchplate STEP/STL/SVG;
- stock regular right-case STL;
- Type-C 25 mm housing STEP/STLs;
- Kivipallur PMW3360 breakout PCB;
- the old mechanical reference audit at commit `432ea630584c22dff2e9f5a596138dcc7602013f`;
- the old Task 3C/3D/3E PCB results as evidence of which stock features actually had to change.

The old scripts and UUID-specific edits are **not** part of the new architecture.

---

# 1. Right-thumb trade study

Stock mapping is:

| Logical key | PCB switch | Diode |
| --- | --- | --- |
| R32 | SW20 | D20 |
| R33 | SW21 | D21 |
| R34 | SW22 | D22 |

The historical trackball placement in KiCad coordinates was:

```text
ball center = (162.323043, 134.748004) mm
```

The audited Type-C housing XY envelope at that placement is approximately:

```text
X = 134.359736 .. 171.954548 mm
Y = 119.749627 .. 149.748004 mm
```

### R34

R34 / SW22 center:

```text
(143.025, 128.770) mm
```

The housing envelope directly occupies the R34 region. R34 therefore conflicts with the minimal-change trackball placement and is the natural key to remove.

### R33

R33 / SW21 center:

```text
(121.915, 131.640) mm
```

Using the same conservative 18 x 18 mm keycap envelope as the historical audit:

- R33 right edge = approximately `130.915 mm`;
- housing left edge = approximately `134.360 mm`;
- conservative horizontal gap = approximately **3.445 mm**.

The full source-mesh audit measured **3.444 mm** minimum XY clearance.

This is important: with R33 retained, the historical placement is already close to the inward geometric limit. The ball can move only about **3.4 mm further inward/left** before the conservative R33 envelope begins to collide.

### R32

R32 / SW20 center:

```text
(102.242846, 139.828264) mm
rotation = 30 deg
```

If R33 were also removed, the next conservative 18 mm rotated-keycap X limit is approximately `114.537 mm`.

Compared with the current housing left edge, that creates approximately **19.8 mm** of additional potential inward movement before R32 becomes the next simple keycap constraint.

That is a meaningful ergonomic design option, but it requires another switch/diode/RGB deletion and more plate/electrical changes.

### Right encoder

Right encoder / SW18 center:

```text
(95.590, 113.950) mm
```

Historical source-mesh clearance from the housing was approximately **27.772 mm**.

Therefore:

> Removing the encoder while retaining R33 does not buy useful trackball movement. R33 remains the active inward constraint.

Encoder removal only becomes relevant after substantially more aggressive thumb-cluster removal and inward trackball movement.

---

## Variant comparison

| Variant | Right thumb keys retained | Right encoder | Product changes | Geometric benefit | Minimal-change result |
| --- | --- | --- | --- | --- | --- |
| A | R32, R33 | retain | remove R34 only | already mechanically valid | **selected baseline** |
| B | R32, R33 | remove | R34 + encoder removed | effectively no benefit while R33 remains | dominated |
| C | R32 | retain | remove R33 + R34 | up to ~19.8 mm additional simple inward keycap envelope before R32, subject to mounts/case | fallback ergonomic option |
| D | R32 | remove | remove R33 + R34 + encoder | only useful if trackball is moved much further inward | more invasive |
| E | none / fewer | optional | major thumb redesign | maximum freedom | outside minimal-change goal |

This is a **minimal-change decision**, not a claim that Variant A is universally the best possible ergonomic trackball location.

---

# 2. Minimal PCB delta

## Preserve

The target right PCB should preserve, unless a downstream numerical check proves otherwise:

- every retained Konrad switch center and rotation;
- R32 / SW20;
- R33 / SW21;
- right encoder location;
- controller location;
- TRRS location;
- existing structural PCB holes;
- stock PCB perimeter everywhere outside the breakout interface;
- matrix topology for retained keys;
- RGB topology concept: one LED per retained key;
- half-duplex split interface.

The left PCB needs **no trackball-driven geometric change**.

## Required right-PCB changes

### 2.1 Remove the R34 circuit

Omit:

- SW22;
- D22;
- the R34 RGB device;
- the local matrix branch that exists only for R34.

The RGB chain must bypass the missing R34 LED.

In the regenerated board this should be expressed directly in the net model, not implemented as a post-generation copper patch.

### 2.2 Add the breakout/service notch

Reference center:

```text
KiCad center = (143.111043, 134.747997) mm
nominal envelope = 2 x 22 mm
```

The stock lower Edge.Cuts in this local region are around:

```text
Y = 139.175891 mm
```

The 22 mm service envelope therefore crosses the stock lower edge. The manufacturable interpretation is an **open edge notch**, not a closed internal slot.

The old implementation proved that the rest of the stock Edge.Cuts can remain unchanged.

### 2.3 Add the 1x7 PMW3360 interface

Required signals:

- CS;
- MISO;
- MOSI;
- SCK;
- MOTION position reserved / NC;
- 3V3;
- GND.

The header itself is required; the old **support tongue is not**.

The historical header midpoint was placed at the breakout Y datum, causing the lower pin(s) to extend beyond the stock lower PCB edge. That forced a local +X support tongue.

For the regenerated board, Task 3 should first attempt to place or rotate the 1x7 header fully inside the stock outline. A modest inward shift of the header row is geometrically plausible and should be evaluated before adding any support tongue.

Therefore the Task-2 geometry contract is:

> Preserve the stock PCB perimeter except for the 2 x 22 breakout notch. Add a connector-support tongue only if Task-3 footprint/clearance validation proves it is necessary.

### 2.4 Add PMW3360 electrical ownership

The historical conflict-free baseline used:

- GP2 = SCK;
- GP3 = MOSI;
- GP4 = MISO;
- GP9 = CS;
- GP1 remains half-duplex split;
- GP0 remains RGB.

Those pins were freed by Rev-1 removal of stock OLED/I2C, PAW3204, audio, and full-duplex RX ownership.

Exact GPIO allocation remains a Task-3 electrical decision, but no additional product feature needs to be removed to obtain a workable PMW3360 interface.

## What is *not* inherently required

The old derivative removed **65 stock segments and 5 vias** before adding PMW routing. That was largely a consequence of preserving and surgically modifying the reversible/universal stock PCB.

A new right-specific generated PCB does **not** need to reproduce that mutation burden.

Likewise, the old 144-segment / 27-via PMW route set is not a target topology. It is evidence that the interface can be routed, not evidence that such routing complexity is required.

---

# 3. Minimal switchplate delta

The switchplate is a much smaller change than a complete redesign.

## Preserve

- stock Konrad plate perimeter;
- stock 1.5 mm reference thickness;
- all eight verified structural case/switchplate mounting axes;
- every retained MX opening;
- encoder opening/interface where applicable.

## R34 opening can be reused

In native switchplate coordinates:

```text
R34/SW22 center ≈ (62.3864, 25.2441)
breakout center ≈ (62.4732, 19.2661)
```

A nominal 14 x 14 mm R34 MX opening spans approximately:

```text
X = 55.386 .. 69.386
Y = 18.244 .. 32.244
```

The 2 x 22 mm breakout corridor spans approximately:

```text
X = 61.473 .. 63.473
Y = 8.266 .. 30.266
```

So approximately **12.0 mm of the 22 mm breakout corridor already lies inside the existing R34 switch opening**.

Only roughly **10 mm** of additional narrow clearance is required in that direction before considering the final edge transition.

This strongly favors reusing/merging the R34 opening into the breakout service geometry rather than rebuilding a large area of the plate.

## Add housing mounting holes

Historical Type-C screw centers in native switchplate coordinates:

```text
(75.4722, 27.2478)
(75.4743, 11.2878)
```

Nominal spacing:

```text
16 mm
```

These screws belong to the **switchplate**, not the main PCB.

The original housing STEP audit found approximately 0.8 mm pilot radius in the source geometry. Final hole diameter must be chosen from the actual screw/insert strategy, but the axes are the important Task-2 datum.

## Switchplate minimal-change target

Therefore the expected switchplate delta is only:

1. retain/reuse the removed R34 opening;
2. extend/merge it into the breakout service clearance;
3. add the two Type-C mounting holes.

No global plate perimeter rewrite is justified by current evidence.

---

# 4. Minimal right-case delta

The stock regular right case is only available as an STL, but the old source-mesh audit already established:

- the placed housing intersects the stock shell;
- all eight structural mounting axes remain clear;
- MCU and TRRS remain clear;
- the collision is localized to shell material around the trackball.

Therefore a full right-case re-author is **not required merely to add the trackball**.

The preferred minimal-change case workflow is:

```text
stock right-case STL
        +
canonical trackball placement
        +
parameterized local clearance solid
        ↓
deterministic boolean subtraction
        ↓
modified right-case STL
```

The placed Type-C housing occupied approximately this native right-case XY region:

```text
X ≈ 134.30 .. 171.90 mm
Y ≈ 60.22  .. 90.20 mm
```

That is a local region of roughly **38 x 30 mm**.

The boolean clearance volume should be derived from the actual placed housing plus manufacturing/assembly clearance, not from a hand-drawn arbitrary box.

A full parametric case reconstruction remains a fallback if mesh boolean quality or future modifications require it; it should not be the default starting point.

The **left case requires zero trackball-driven change**.

---

# 5. Minimal-change geometry contract

The initial Task-2 canonical model should reproduce the already-validated placement:

```text
ball center, KiCad:          (162.323043, 134.748004)
housing screw midpoint:      (156.111043, 134.748004) approx
breakout/service center:     (143.111043, 134.747997)
sensor direction:            toward -X in fabrication frame
housing screw pair axis:     Y
housing screw spacing:       16 mm
```

These values are the **starting canonical baseline**, not hand-edited production coordinates.

The Ergogen model should express them relationally:

```text
ball_center
  ├─ housing_screw_midpoint = ball_center + housing_screw_offset
  │    ├─ screw_1 = midpoint + screw_axis * 8 mm
  │    └─ screw_2 = midpoint - screw_axis * 8 mm
  └─ breakout_center = screw_midpoint + sensor_direction * 13 mm
```

The old absolute values then become regression checks rather than the design mechanism.

---

# 6. Preserve/change boundary for the new architecture

## Preserve exactly where practical

- left-half geometry;
- retained Konrad key centers/rotations;
- R32 and R33;
- right encoder;
- controller;
- TRRS;
- structural mount axes;
- stock right PCB outline outside the service notch;
- stock plate perimeter;
- case support/stack-up geometry outside local shell relief.

## Change intentionally

- delete R34/SW22/D22;
- delete its RGB element;
- add PMW connector and nets;
- add 2 x 22 breakout notch;
- add switchplate housing screw axes;
- merge/extend R34 plate opening into service clearance;
- subtract local right-case housing clearance.

## Do not carry forward by default

- historical PCB UUID surgery;
- historical 65-segment / 5-via cleanup;
- historical 144-segment PMW routing;
- connector support tongue;
- whole-case CAD reconstruction;
- any movement of structural mounting axes;
- right-encoder removal.

---

# 7. Task 2 implementation sequence

## Task 2A — Minimal-change study

**Complete.**

This document and `minimal-change-baseline.yaml` define the implementation hypothesis.

## Task 2B — Reconstruct preserved stock geometry

In Ergogen, reconstruct and numerically validate:

- all retained Konrad key points;
- right encoder reference;
- MCU/TRRS;
- structural axes;
- stock PCB perimeter;
- stock switchplate perimeter.

No trackball modification should be necessary to pass this phase.

## Task 2C — Overlay minimal trackball delta

Add parametrically:

- R34 suppression;
- ball center;
- housing envelope;
- screw pair;
- breakout/service corridor;
- PCB notch;
- plate service extension;
- PMW header placement envelope.

Run numerical collision/clearance checks against the preserved stock geometry.

## Task 2D — Freeze canonical geometry

Task 2 is complete when:

- preserved geometry matches stock numerically;
- Variant A remains collision-free in the regenerated model;
- the PCB delta is local;
- the plate delta is local;
- all eight structural axes remain unchanged;
- the right-case modification is demonstrated to be local shell relief;
- the final PMW header can either fit inside the stock board outline or any required local support addition is explicitly justified;
- the final right-thumb architecture is frozen for Task 3.


---

# Revision 3 correction — PCB trackball cavity

Revision 2 proved the connector handedness and the Type-C/Kivipallur placement, but it preserved too much of the stock PCB around the ball.

The revision-2 board composition was:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot   # 2 x 22 mm only
```

That model treats the Type-C housing envelope as a reference drawing only; it never subtracts a mechanical cavity from the PCB. The resulting right PCB therefore leaves substantial FR-4 under/around the trackball housing.

The checked-in KLORBall-35 right PCB uses a different topology: a **large open-edge cavity** around the ball/housing, while a narrow right-side peninsula carries the PMW connector. This is the mechanical topology Revision 3 must reproduce.

## Invalidated assumption

The earlier statement that the old implementation proved the stock Edge.Cuts could remain unchanged except for the 2 x 22 mm service notch is no longer accepted as the production geometry contract.

The 2 x 22 mm corridor remains useful as the breakout/service datum, but it is insufficient as the complete PCB clearance feature.

## Revision-3 requirements

Revision 3 must:

- keep the revision-2 ball, housing, breakout, and PMW connector handedness/relative placement unless the new cavity proves a local conflict;
- retain R32/SW20 and R33/SW21;
- keep R34/SW22/D22 removed;
- retain the right encoder, MCU, TRRS, and structural mounting axes where mechanically valid;
- replace the notch-only PCB delta with an open-edge cavity derived from the Type-C housing and checked against KLORBall-35 topology;
- retain a mechanically valid right-side PMW connector peninsula/support region;
- validate explicit FR-4 clearance around the ball/housing rather than relying on a reference outline;
- re-run Task 2B/2C/2D and Task 3D generation after the cavity is frozen.

The cavity is a mechanical change only. Task-3 electrical ownership and PMW pin order remain unchanged.
