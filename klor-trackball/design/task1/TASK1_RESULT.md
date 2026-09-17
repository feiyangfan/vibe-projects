# Task 1 result — mechanical reference assembly

Status: **complete — placement locked**.

The candidate trackball placement from the handoff is mechanically valid and did not need to move. The full source-geometry audit passed on GitHub Actions after verifying the checked-in Type-C source files, resolving the coordinate frames, reconstructing the stock case/switchplate stack, and checking retained components and structural fasteners.

## Locked fabrication datums

Canonical frame: **KLOR Gerber/Excellon fabrication XY**, millimetres.

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | 162.323 | -134.748 |
| Housing screw midpoint | 156.111 | -134.748 |
| Housing screw 1 | 156.111 | -126.768 |
| Housing screw 2 | 156.111 | -142.728 |
| Breakout-slot center | 143.111 | -134.748 |
| Deleted SW22/R34 center | 143.025 | -128.770 |

The deleted-switch datum resolves to the source PCB footprint `SW22` with approximately **0.000045 mm** coordinate error.

## Coordinate transforms

### KiCad PCB → Gerber/Excellon

Solved from all 21 MX switch centers in the NPTH drill file:

```text
R = [[ 1.000000000,  0.000000342],
     [ 0.000000342, -1.000000000]]
t = [-0.000089, -0.000052] mm
```

21/21 centers matched, RMS residual **0.000181 mm**. Practically, the fabrication frame is the KiCad frame with Y reflected.

### KiCad PCB → native Konrad switchplate STL

Solved from the 18 Konrad MX openings:

```text
R = [[ 0.999999991,  0.000131877],
     [ 0.000131877, -0.999999991]]
t = [-80.655587, 153.995244] mm
```

18/18 openings matched, RMS residual **0.020019 mm**.

### Native switchplate → native right-case STL

Solved from the eight structural M2 mounting axes:

```text
R = [[ 0.999999999,  0.000033962],
     [-0.000033962,  0.999999999]]
t = [80.582795, 55.951799] mm
```

8/8 axes matched, RMS residual **0.006063 mm**.

## Stock stack-up

The stock right-case support surface is at native case `Z = -0.8 mm`. KLOR specifies 7 mm M2 standoffs and the stock 3DP switchplate is 1.5 mm thick.

Therefore:

- switchplate bottom: case `Z = 6.2 mm`
- switchplate top / Type-C mounting plane: case `Z = 7.7 mm`
- stock case top: `Z = 8.800025 mm`
- stock case lip above switchplate: approximately **1.100 mm**

The Type-C housing mounting plane aligns to switchplate top. The 25 mm ball top is at case `Z = 38.2 mm`; the housing rim top is at approximately `Z = 38.9 mm`, leaving the ball approximately **0.7 mm below the rim**.

## Locked placement in source-model frames

Ball center:

- KiCad: `(162.323043, 134.748004)`
- native switchplate: `(81.685225, 19.268648)`
- native right case: `(162.268674, 75.217672)`

Housing screw centers in native switchplate coordinates:

- `(75.472175, 27.247831)`
- `(75.474275, 11.287831)`

Breakout-slot center:

- native switchplate: `(62.473225, 19.266121)`
- native right case: `(143.056674, 75.215798)`

Type-C right-housing bounds after placement, native switchplate frame:

```text
min = (53.72126, 4.27051, 1.5)
max = (91.31534, 34.24435, 32.7)
```

## Clearance results

The closest retained switch/keycap envelopes clear the housing using a conservative 18 × 18 mm keycap XY envelope:

- `SW15`: **2.654 mm** minimum XY gap
- `SW21`: **3.444 mm** minimum XY gap
- next closest `SW13`: **4.022 mm**
- next closest `SW12`: **4.424 mm**

Other conservative XY clearances:

- right encoder `SW18`: **27.772 mm**
- MCU `U1` / ProMicro region: **40.321 mm**
- TRRS `J1`: **46.460 mm**

All eight structural M2 axes were checked against the actual placed housing mesh using a deliberately conservative fastener envelope:

- M2 head: 4.5 mm diameter × 2.0 mm high
- below-plate boss: 6.1 mm diameter
- fastener-head collisions: **0 / 8**
- below-plate boss collisions: **0 / 8**
- closest structural axis has approximately **9.159 mm** radial distance to a housing vertex in the first 3 mm above the plate

## Breakout/service path

The Kivipallur breakout Edge.Cuts measure **22 × 25 mm**. The Klorball reference pass-through is **2 × 22 mm**.

The 22 mm breakout short edge is aligned to the 22 mm slot dimension and the 2 mm slot dimension clears PCB thickness. The slot corridor has approximately **8.000 mm** minimum clearance to the retained conservative keycap envelopes. The breakout extends inward along the sensor direction and is serviceable from that direction.

## Stock right-case collision

The unmodified stock right-case shell **does intersect the Type-C housing** at the locked placement. This is expected and is not a Task 1 placement failure:

- all eight structural case/switchplate mounting axes remain clear;
- retained switches, encoder, MCU, and TRRS remain clear;
- the interference is local shell material around the trackball region.

Therefore later case work must provide **local shell relief around the housing**, while preserving the existing structural mounting axes. The placement must not be moved merely to avoid modifying the stock shell.

## Completion gate

All required Task 1 gates pass:

- housing source hashes verified
- Gerber ↔ KiCad frame verified
- PCB ↔ switchplate frame verified
- switchplate ↔ case frame verified
- stock standoff/plate Z stack verified
- nearest retained switches clear
- encoder clear
- MCU clear
- TRRS clear
- all eight structural mount axes / conservative fastener envelopes clear
- breakout orientation and service path verified
- housing mounting plane verified
- ball exposure verified

**`placement_locked: true`**

The CI evidence is generated by `.github/workflows/klor-task1-mechanical-audit.yml`; the authoritative final gate is `design/task1/generated/task1-final-gate.json` in the workflow artifact.
