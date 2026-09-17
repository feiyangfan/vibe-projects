# Task 2C result — Kivipallur connector contract

Status: **complete**.

Task 2C audits the actual Kivipallur PMW3360 breakout and the working Klorball35 right-hand PCB/schematic. It locks the connector footprint, breakout pin numbering, keyboard-side pin numbering, board sides, mating handedness, MOTION disposition, and service orientation that Task 3 must preserve.

No production KLOR PCB geometry is modified by this task.

## Sources

- `klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb`
- `klorball35/kicad/klorball35_right/klorball35_right.kicad_pcb`
- `klorball35/kicad/klorball35_right/klorball35_right.kicad_sch`
- `klorball35/config.yml`
- `design/task1/reference_assembly_manifest.yaml`
- `design/task2/audit_task2c_kivipallur_connector.py`
- `.github/workflows/klor-task2c-kivipallur-connector-audit.yml`

The Task 2C CI audit passes every locked source-topology assertion.

## Breakout connector — authoritative Kivipallur side

The Kivipallur breakout uses:

- reference: `J1`
- footprint: `Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical`
- topology: 1 × 7 through-hole
- pitch: **2.54 mm**
- footprint side: **B.Cu**
- PMW3360 `U2` side: **B.Cu**
- breakout outline: **22 × 25 mm**

Exact breakout pin order:

| Kivipallur J1 pin | Signal |
| ---: | --- |
| 1 | GND |
| 2 | +3V3 |
| 3 | MOTION |
| 4 | SCK |
| 5 | MOSI |
| 6 | MISO |
| 7 | CS |

The header lies along the trailing short edge of the breakout. In the checked-in breakout coordinates, J1 pin 1 is at `(118.64, 73.40)` and pin 7 at `(103.40, 73.40)`; the PMW3360 is inward from that edge.

## Working Klorball35 keyboard-side mate

The Klorball35 right PCB uses the same 1 × 7 / 2.54 mm footprint as `J2`, but on **F.Cu** and with the physical pin order deliberately reversed:

| Klorball35 J2 pin | Net / state |
| ---: | --- |
| 1 | CS |
| 2 | MISO |
| 3 | MOSI |
| 4 | SCK |
| 5 | NC |
| 6 | +3V3 |
| 7 | GND |

The schematic explicitly leaves the MOTION mate unconnected. This is not an accidental unrouted net: revision 1 intentionally does not use MOTION.

This reversed keyboard-side numbering is required by the physical mating orientation. Copying the breakout's `1=GND ... 7=CS` order onto the KLOR main PCB would be wrong for the proven opposite-facing assembly.

## Opposite-facing mating contract

The proven mate is:

| Kivipallur J1 | Signal | Keyboard-side connector |
| ---: | --- | ---: |
| 1 | GND | 7 |
| 2 | +3V3 | 6 |
| 3 | MOTION | 5 = NC |
| 4 | SCK | 4 |
| 5 | MOSI | 3 |
| 6 | MISO | 2 |
| 7 | CS | 1 |

Rule:

```text
breakout pin N <-> keyboard pin (8 - N)
```

That produces a signal-for-signal mate with no crossed wiring while keeping the breakout and keyboard connector on opposite-facing component sides.

## 2 × 22 mm reference guide

`klorball35/config.yml` defines `trackball_breakout_right` as a **2 × 22 mm** rectangle and emits it on **`Cmts.User`**. The generated Klorball35 right PCB contains exactly one matching 2 × 22 mm `Cmts.User` guide.

Important distinction:

- the 2 × 22 mm item is a **mechanical placement/insertion guide** in the reference design;
- it is **not itself an Edge.Cuts fabrication slot**;
- Task 3 must create the real KLOR PCB pass-through / edge clearance at the Task 1-locked breakout datum.

The reference `J2` row is parallel to the guide long axis. Its midpoint is offset from the guide center by **4.613622 mm**. The source audit records this as reference mating geometry rather than pretending the header is centered in the guide.

## Locked KLOR right-hand orientation

Task 1 already locks:

- breakout guide/slot center in canonical KLOR Gerber/Excellon XY: `(143.111, -134.748)`
- slot long dimension: **22 mm**, along global Y
- sensor/service direction: **negative global X**

Task 2C locks the KLOR connector orientation relative to that frame:

- use the same `PinHeader_1x07_P2.54mm_Vertical` footprint family;
- keyboard-side connector is on **F.Cu**;
- connector row is parallel to the 22 mm guide/slot long axis;
- connector is on the **positive-X / non-sensor side** of the guide, so breakout insertion/service proceeds across the guide toward negative X;
- preserve the working Klorball35 handedness: in canonical Gerber view, **pin 1 is the negative-Y end and pin 7 is the positive-Y end**;
- therefore the physical KLOR row from negative Y to positive Y is:

```text
pin 1  CS
pin 2  MISO
pin 3  MOSI
pin 4  SCK
pin 5  NC / breakout MOTION
pin 6  3V3
pin 7  GND
```

Because the KLOR KiCad → Gerber transform reflects Y, the native KiCad view shows the opposite vertical ordering. Task 3 must use the canonical Gerber orientation above (or the verified Task 1 transform) rather than visually copying screen-up/down from a different PCB.

The Klorball35 measured header-to-guide separation of **4.613622 mm** is the Task 3 starting placement relationship. Task 3 owns the final production XY footprint placement and must verify connector-body, breakout, housing, routing, and board-edge clearances; it may not flip the connector side, pin order, row handedness, or mating rule without reopening Task 2C.

## Revision-1 connector contract entering Task 2D

The connector-level contract is now unambiguous:

| KLOR connector pin | Breakout signal | Revision-1 state |
| ---: | --- | --- |
| 1 | CS | used |
| 2 | MISO | used |
| 3 | MOSI | used |
| 4 | SCK | used |
| 5 | MOTION | NC |
| 6 | 3V3 | used |
| 7 | GND | used |

Task 2D will attach the already-audited KLOR MCU/net ownership to this fixed physical connector order.

## Completion gate

Task 2C passes:

- Kivipallur connector footprint and 2.54 mm pitch resolved;
- breakout J1 pins 1–7 resolved from source;
- keyboard-side J2 pins 1–7 resolved from the working Klorball35 reference;
- breakout B.Cu / keyboard F.Cu side relationship resolved;
- opposite-facing `N <-> 8-N` mate verified signal-for-signal;
- MOTION → keyboard pin 5 → NC verified in the reference schematic;
- 22 × 25 mm breakout outline verified;
- 2 × 22 mm reference guide and its `Cmts.User` status verified;
- header row/guide parallelism and 4.613622 mm reference offset verified;
- KLOR target row axis, side of guide, pin-1 end, pin-7 end, and negative-X service direction locked against the Task 1 canonical frame.

**Task 2C: COMPLETE.**

Next dependency: **Task 2D — freeze the PCB net contract.**
