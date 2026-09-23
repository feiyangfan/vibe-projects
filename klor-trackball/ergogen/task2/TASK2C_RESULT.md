# Task 2C Result — Minimal Trackball Delta

## Status

**PASS — Task 2C is complete.**

Task 2C layers the minimum required trackball geometry on top of the separately validated Task-2B stock model.

The design is no longer expressed as a set of absolute KiCad edits. The ball center is the root trackball datum and the housing, screw pair, breakout corridor, PMW header reference, and support tongue are derived from it.

## Passing source state

Branch:

`klor-trackball/task2-minimal-change`

Passing head:

`98c35cdf700785a2fd9d587f025f4ce8f7935e66`

GitHub Actions:

- workflow: `KLOR Task 2C - trackball delta`
- run ID: `35804745592`
- job ID: `107002903566`
- conclusion: **success**

Generated artifact:

- name: `klor-task2c-trackball-geometry`
- artifact ID: `10727496484`
- SHA-256: `61fca51e9835cf27450aa11afb0d8f283856de51200f7624602dac4d52feddca`

The workflow:

1. generates Ergogen twice;
2. proves deterministic output;
3. re-runs the full Task-2B preservation regression;
4. validates the Task-2C delta;
5. uploads the generated geometry.

## Preserved Task-2B foundation

The Task-2C workflow re-runs `validate_task2b.py` before validating any trackball-specific geometry.

Result: **PASS**.

Therefore Task 2C did not alter:

- the 20-key stock Konrad reference layer;
- right encoder;
- MCU/TRRS datums;
- MH1..MH9;
- eight structural case/switchplate axes;
- stock PCB Edge.Cuts source paths;
- stock switchplate perimeter source path.

The target variant is created as a new composition on top of those preserved definitions.

## Final right-thumb architecture entering Task 2D

The Task-2C target is:

- retain R32 / `SW20`;
- retain R33 / `SW21`;
- suppress R34 / `SW22`;
- retain the right encoder;
- 19 right-half keys;
- 39 total keys using the existing 20-key left half.

`SW22` remains available only as a stock reference datum so the previous R34 aperture can be reused mechanically. It is excluded from the target key-cutout selector.

## Canonical trackball relationships

Canonical frame:

- origin = stock `SW13`;
- +X = stock KiCad +X;
- +Y = reflected KiCad Y, positive upward.

Trackball root datum:

```text
ball_center = (22.261644, -28.000147)
```

Historical Task-1 placement regression: **PASS**.

Derived relationships:

```text
housing_center
    = ball_center + (-9.165901, -0.000812)

housing_screw_midpoint
    = ball_center + (-6.212, 0)

housing_screw_1
    = housing_screw_midpoint + (0, +7.98)

housing_screw_2
    = housing_screw_midpoint + (0, -7.98)

breakout_center
    = ball_center + (-19.212, 0)

pmw_header_center
    = breakout_center + (4.613622, 0)
```

Validated source-geometry screw spacing: **15.96 mm**.

The tiny historical transform residual between the breakout and ball Y coordinates is intentionally normalized out as sub-micron frame noise.

## Housing envelope

The source-audited Type-C housing XY envelope is represented relative to the ball center.

Reference size:

```text
37.594812 × 29.998377 mm
```

The conservative retained-key clearance check passes.

Closest retained key under the simple 18 × 18 mm XY envelope:

```text
SW15 gap = 2.629627 mm
```

This is consistent with the earlier source-mesh audit and remains above the Task-2C regression floor.

## Breakout/service corridor

The breakout service corridor is:

```text
2 × 22 mm
axis: Y
service direction: -X
```

The validator proves that it crosses the stock lower PCB edge. Therefore the fabrication geometry is an **open edge notch**, not a closed internal slot.

The target PCB is composed declaratively as:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

No stock KiCad UUID or Edge.Cuts object is mutated.

## PMW header support conclusion

Task 2A left the support tongue conditional because a regenerated design should not inherit old geometry without proof.

Task 2C now supplies that proof.

The locked Kivipallur mating relationship requires:

- 1 × 7 header;
- 2.54 mm pitch;
- row axis parallel to the 22 mm service corridor;
- row midpoint offset +4.613622 mm from the corridor center.

Using the nominal 2.54 × 17.78 mm header-body reference envelope:

```text
stock lower edge at header X  = -32.428034
header body bottom            = -36.890147
required overhang             =   4.462113 mm
```

So the connector cannot remain fully on the stock outline while preserving the locked mating geometry.

The support extension is therefore **required**, not historical baggage.

It is encoded as one local parameterized rectangle:

```text
size = 5.888957 × 5.074109 mm
```

The validator confirms that it:

- joins the stock lower edge;
- covers the complete header width;
- extends deep enough for the header envelope;
- does not require unrelated outline changes.

This replaces the old UUID-based Task-3D Edge.Cuts surgery with an upstream geometric relation.

## Switchplate delta

The stock switchplate perimeter remains unchanged.

The target plate service opening is defined by combining:

1. the existing stock R34 / SW22 14 × 14 mm aperture;
2. the 2 × 22 mm breakout corridor.

This reuses already-open material and adds only the narrow missing service extension.

Two Type-C housing screw axes are also canonical Task-2 points. Final hole diameter remains a Task-5 fabrication/detail decision; the axes are frozen here.

## Generated outputs

Task 2C generates:

- canonical trackball points;
- 25 mm ball reference;
- housing envelope;
- housing screw axes;
- breakout/service corridor;
- PMW header envelope;
- local support tongue;
- target 19-key right-half cutout reference;
- merged plate service opening;
- target PCB Edge.Cuts;
- combined Task-2C preview;
- KiCad 8 trackball-reference PCB scaffold.

Generated output remains disposable and ignored.

## Completion gate

| Gate | Result |
| --- | --- |
| Clean Ergogen generation succeeds | PASS |
| Two generation passes are deterministic | PASS |
| Complete Task-2B preservation gate still passes | PASS |
| Ball placement matches Task-1 historical regression | PASS |
| Breakout placement matches historical regression | PASS |
| Housing/screw/breakout/header relationships are parametric | PASS |
| R34/SW22 is the only target key suppressed | PASS |
| Right encoder remains retained | PASS |
| 2 × 22 corridor is proven to be an open-edge notch | PASS |
| Support tongue necessity is numerically demonstrated | PASS |
| Support tongue covers the required header envelope | PASS |
| Plate reuses R34 aperture + local corridor only | PASS |
| Conservative retained-key/housing clearance passes | PASS |
| Generated KiCad/DXF outputs exist | PASS |

## Architectural conclusion

The Task-2 geometry now has a clean two-layer structure:

```text
Task 2B: exact preserved stock geometry
                +
Task 2C: bounded parametric trackball delta
                =
Task 2D freeze candidate
```

The old implementation is now used as regression evidence only. Its mechanically necessary result—the small PMW connector support extension—has been re-derived and represented parametrically.

## Next

Proceed to **Task 2D — freeze the canonical geometry and contract entering Task 3**.
