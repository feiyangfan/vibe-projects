# Task 2D Result — Canonical Geometry Freeze

## Status

**PASS — Task 2 is complete and the Rev-1 canonical geometry is frozen for Task 3.**

Task 2D does not introduce a new geometry design. It converts the validated Task-2B stock layer and Task-2C trackball delta into an explicit change-controlled contract.

## Freeze proof

Passing head:

`513938321ac88855f08606424d25d2d5765a1bd6`

GitHub Actions:

- workflow: `KLOR Task 2D - geometry freeze`
- run ID: `35805288093`
- job ID: `107004623603`
- conclusion: **success**

Artifact:

- name: `klor-task2d-frozen-geometry`
- artifact ID: `10727552547`
- SHA-256: `b0c2462e2c68786aab1fabd6a46be95fa38adae95a72b236bd0cf2ce198cc61b`

The gate performs two clean Ergogen generations, proves deterministic output, re-runs the complete Task-2B and Task-2C validators, then validates the Task-2D freeze contract.

## Product geometry frozen

Rev-1 geometry is now:

- KLOR 1.4 MX / fixed Konrad;
- 20 keys left;
- 19 keys right;
- 39 keys total;
- retain R32 / SW20;
- retain R33 / SW21;
- remove R34 / SW22 / D22;
- retain the right EC11 encoder at its stock location;
- 20 RGB devices left and 19 right.

`REQUIREMENTS.md` has been updated so these are no longer described as Task-2 candidates.

## Preserved stock layer

The complete Task-2B preservation gate passes inside the Task-2D workflow.

Frozen preserved geometry includes:

- all retained key centers and rotations;
- right encoder location;
- MCU location;
- TRRS location;
- MH1..MH9;
- eight case/switchplate structural axes;
- exact stock PCB source contours outside the approved local trackball delta;
- exact stock switchplate outer perimeter.

## Trackball geometry frozen

Canonical frame:

- origin = SW13;
- +X = stock KiCad +X;
- +Y = reflected stock KiCad Y.

Frozen root datum:

```text
ball_center = (22.261644, -28.000147)
```

Frozen relational geometry:

```text
housing_center
  = ball_center + (-9.165901, -0.000812)

housing_screw_midpoint
  = ball_center + (-6.212, 0)

housing_screw_1
  = midpoint + (0, +7.98)

housing_screw_2
  = midpoint + (0, -7.98)

breakout_center
  = ball_center + (-19.212, 0)

pmw_header_center
  = breakout_center + (4.613622, 0)

pmw_support_tongue_center
  = breakout_center + (3.9444785, -6.9649485)
```

Housing screw-axis spacing is frozen at **15.96 mm**.

## Frozen PCB mechanical composition

The right PCB geometry is:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

The service corridor is frozen at **2 × 22 mm**, aligned to Y and implemented as an open-edge notch.

The local PMW support tongue is frozen because the locked mating geometry proves the connector body overhangs the stock lower edge by about **4.462 mm**.

No unrelated stock perimeter modification is authorized.

## Frozen switchplate interface

The stock switchplate outer perimeter and eight structural axes remain fixed.

The trackball service opening is:

```text
existing R34 / SW22 14 × 14 opening
+ 2 × 22 breakout corridor
```

Two Type-C housing screw axes are frozen.

The final production drill diameter is intentionally deferred to Task 5; that is a fabrication-detail decision and does not move the frozen axes.

## Frozen PMW mechanical/physical connector contract

The keyboard-side interface entering Task 3 is:

- 1 × 7, 2.54 mm vertical through-hole header;
- F.Cu;
- row axis parallel to Y;
- row center offset +4.613622 mm from the breakout center;
- physical order from negative Y to positive Y:

| Pin | Signal |
| ---: | --- |
| 1 | CS |
| 2 | MISO |
| 3 | MOSI |
| 4 | SCK |
| 5 | NC / MOTION |
| 6 | 3V3 |
| 7 | GND |

Mating rule:

```text
breakout pin N <-> keyboard pin (8 - N)
```

Exact MCU GPIO ownership remains a Task-3 electrical decision.

## Task-3 change boundary

Task 3 may:

- select a production RP2040 Pro-Micro-compatible controller within the frozen envelope;
- implement production footprints;
- define matrix/RGB/split/encoder/PMW nets;
- choose final GPIO ownership consistent with requirements;
- generate the left/right unrouted electrical PCBs;
- add copper keepouts required by the frozen mechanics.

Task 3 may **not** silently:

- move retained keys;
- restore R34 or remove R32/R33;
- move/remove the right encoder;
- move MCU/TRRS or structural axes;
- move the ball, housing, breakout, PMW header reference, or support tongue;
- change the 2 × 22 corridor;
- change the stock board outside the approved local delta;
- change the switchplate outer perimeter;
- change PMW connector side, row axis, or physical pin order.

Any such change requires reopening Task 2 and updating the freeze contract.

## Deferred details

The following are deliberately not frozen as Task-2 geometry:

- final housing screw drill diameter — Task 5;
- exact right-case boolean clearance margin — Task 6;
- exact controller variant — Task 3;
- final GPIO allocation — Task 3;
- copper routing/zones — Task 4;
- fabrication tolerances not already required by mechanical fit.

## Completion gate

| Gate | Result |
| --- | --- |
| Deterministic Ergogen regeneration | PASS |
| Complete Task-2B stock regression | PASS |
| Complete Task-2C trackball regression | PASS |
| Requirements contain no unresolved Task-2 choices | PASS |
| 20 / 19 / 39 key architecture frozen | PASS |
| R32/R33 retained, R34 removed | PASS |
| Right encoder retained | PASS |
| RGB counts frozen at 20 / 19 | PASS |
| Trackball relational geometry frozen | PASS |
| PCB notch/support composition frozen | PASS |
| Switchplate local delta frozen | PASS |
| PMW physical connector contract frozen | PASS |
| Task-3 geometry boundary explicit | PASS |
| Deferred downstream details explicit | PASS |

## Next

Proceed to **Task 3 — production footprints, electrical ownership, and generated unrouted PCB**.
