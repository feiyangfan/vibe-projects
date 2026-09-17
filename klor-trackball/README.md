# KLOR Trackball

## Goal

Modify the **right half** of **KLOR 1.4 MX** using the **Konrad** layout so it gains a 25 mm PMW3360 trackball based on the Klorball35 / Kivipallur architecture, while preserving the stock KLOR design everywhere that does not conflict with the trackball.

The **left half remains stock**.

## Implementation baseline

All implementation work starts from `main`.

The old branch `klor-trackball/konrad-trackball-implementation` is **not part of the baseline** and should be ignored unless explicitly re-evaluated.

Reference sources that remain unchanged:

- `klor1.4/` — stock KLOR 1.4 source/reference
- `klorball35/` — working trackball/reference architecture

Modified PCB, CAD, and firmware artifacts must be trackball-specific derivatives rather than silent replacements of the stock source files.

---

## Current status

### Task 1 — mechanical reference assembly: COMPLETE

All subtasks `1A → 1G` passed and the original candidate trackball placement is mechanically locked.

Canonical Task 1 evidence:

- [`design/task1/TASK1_RESULT.md`](design/task1/TASK1_RESULT.md)
- [`design/task1/TASK1B_RESULT.md`](design/task1/TASK1B_RESULT.md)
- [`design/task1/reference_assembly_manifest.yaml`](design/task1/reference_assembly_manifest.yaml)
- `.github/workflows/klor-task1-mechanical-audit.yml`

Locked fabrication frame: **KLOR Gerber/Excellon XY**, millimetres.

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Housing screw 1 | **156.111** | **-126.768** |
| Housing screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |
| Deleted SW22 center | **143.025** | **-128.770** |

Verified coordinate solves:

- KiCad → Gerber: 21 matched MX centers, RMS **0.000181 mm**
- KiCad → switchplate: 18 matched MX openings, RMS **0.020019 mm**
- switchplate → right case: 8 structural mounting axes, RMS **0.006063 mm**
- composed PCB → right-case conservative residual bound: **≤ 0.026082 mm**

Verified mechanical findings:

- Type-C housing mounting plane = switchplate top at case `Z = 7.7 mm`
- ball top = case `Z = 38.2 mm`
- housing rim ≈ case `Z = 38.9 mm`
- nearest retained keycap gap: `SW15` **2.654 mm**
- next retained keycap gap: `SW21` **3.444 mm**
- right encoder `SW18`: **27.772 mm** clearance
- MCU `U1`: **40.321 mm** clearance
- TRRS `J1`: **46.460 mm** clearance
- structural fastener collisions: **0 / 8**
- structural boss collisions: **0 / 8**
- breakout service corridor minimum retained-keycap clearance: approximately **8.000 mm**

The unmodified stock right-case shell **does intersect the Type-C housing locally**. This is an expected downstream case-relief requirement, not a placement failure: all eight structural mounting axes and all retained components remain clear. Do not move the locked trackball placement merely to avoid that local shell relief.

Task 1 result: **`placement_locked: true`**.

### Task 2 — electrical and firmware interface: IN PROGRESS

Task 2 is decomposed as:

`2A → 2B → 2C → 2D → 2E → 2F`

Current state:

- **2A complete** — removed-key circuit audited and disposition locked
- **2B complete** — GPIO ownership and split/TRRS routing audited and disposition locked
- **2C next** — Kivipallur connector footprint/pin order/orientation
- 2D–2F not started

Canonical Task 2 files:

- [`design/task2/TASK2A_RESULT.md`](design/task2/TASK2A_RESULT.md)
- [`design/task2/TASK2B_RESULT.md`](design/task2/TASK2B_RESULT.md)
- [`design/task2/task2_manifest.yaml`](design/task2/task2_manifest.yaml)
- `design/task2/audit_task2a_removed_key.py`
- `design/task2/audit_task2b_gpio_trrs.py`
- `.github/workflows/klor-task2a-electrical-audit.yml`
- `.github/workflows/klor-task2b-gpio-trrs-audit.yml`

The overall keyboard is **not fabrication-locked**. PCB, switchplate, case, firmware, and final integrated validation remain.

Canonical project references:

- [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md)
- [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml)

---

## Locked design direction

### Keyboard

- Base: **KLOR 1.4 MX**
- Layout: **Konrad**
- Left half: stock
- Final target: **39 keys** = 20 left + 19 right
- Keep right encoder
- Keep R32 and R33
- Remove logical key **R34**, implemented on the PCB as `SW22`, firmware matrix position `[7,1]`
- Preserve all other unaffected MX and south-facing SK6812 Mini-E positions

`R34` is the logical Konrad key position; it is **not** a KiCad resistor reference.

### Trackball stack

- ball: 25 mm
- sensor: PixArt PMW3360DM-T2QU
- breakout: Kivipallur PMW3360
- housing: kepeo **Keyball 25mm Trackball Case Type C**, Thingiverse 6719828

Important Type-C values:

- ball center = CAD origin
- housing envelope ≈ **37.595 × 29.998 × 31.200 mm**
- housing/switchplate mounting plane ≈ **18 mm below ball center**
- real 25 mm ball top = **30.5 mm above the mounting plane**
- mounting screw pair = **15.96 mm measured / 16 mm nominal**
- screw-pair midpoint ≈ **6.212 mm toward the sensor side from ball center**

The Type-C housing screws belong to the **switchplate/housing interface**, not the main PCB. The main PCB needs Kivipallur breakout clearance/pass-through plus its electrical interface.

---

## Sequential implementation plan

Do the tasks in dependency order. A later task must not build on an unverified output of an earlier task.

### Task 1 — Build and lock the mechanical reference assembly — COMPLETE

Dependency chain:

`1A → 1B → 1C → 1D → 1E → 1F → 1G`

All gates pass. See [`design/task1/README.md`](design/task1/README.md).

If the locked XY placement ever changes, rerun Task 1A–1G and update together:

- `design/task1/reference_assembly_manifest.yaml`
- `design/konrad_trackball_geometry.yaml`
- `docs/KONRAD_TRACKBALL_HANDOFF.md`

### Task 2 — Lock the electrical and firmware interface — IN PROGRESS

Task 2 converts the current electrical proposal into one source-backed implementation contract before production PCB editing begins.

Dependency chain:

`2A → 2B → 2C → 2D → 2E → 2F`

#### Task 2A — Audit the removed-key circuit — COMPLETE

Logical R34 is PCB `SW22`, a combined MX + SK6812 footprint.

Matrix topology:

```text
col1 -> SW22 -> Net-(D22-A) -> D22 -> row3
```

Locked matrix disposition:

- delete `SW22`
- delete `D22`
- delete the obsolete local `Net-(D22-A)` copper
- preserve `col1` and `row3` trunks
- **do not bridge matrix nets**

RGB topology:

```text
SW13 DOUT -> SW22 DIN -> SW22 DOUT -> SW14 DIN
```

Locked RGB bypass:

```text
SW13 DOUT -> SW14 DIN
```

SW22 RGB power is ordinary shared `VCC`/`GND`; remove only SW22-local branches and preserve shared rail continuity.

**Gate: passed.** See [`design/task2/TASK2A_RESULT.md`](design/task2/TASK2A_RESULT.md).

#### Task 2B — Audit GPIO ownership and split/TRRS routing — COMPLETE

The stock source resolves the proposed PMW GPIOs as follows:

| GPIO | Stock PCB net / stock use | Revision-1 owner | Locked disposition |
| --- | --- | --- | --- |
| GP1 | `TX` → `J1.4`, active half-duplex split | split serial | preserve |
| GP2 | `SDA`, I2C + PAW3204 SDIO | PMW3360 SCK | disable stock I2C/PAW3204; legacy I2C jumpers stay open |
| GP3 | `SCL`, I2C + PAW3204 SCLK | PMW3360 MOSI | disable stock I2C/PAW3204; `J2` haptic DNP; jumpers stay open |
| GP4 | `RX` → `J1.3`, optional full-duplex split path | PMW3360 MISO | make `J1.3` NC and remove exact verified branch |
| GP9 | `AUDIO` → `BZ1.1` | PMW3360 CS | disable audio; `BZ1` DNP/no active audio load |

Exact GP4/TRRS isolation locked by the PCB source:

```text
net: RX (28)
layer: F.Cu
width: 0.254 mm
from: (92.700, 127.025)
to:   (90.880, 127.025)
```

Task 3 must remove that `J1.3`-adjacent branch while preserving GP1 `TX -> J1.4` for half-duplex split transport. Firmware-only disabling of full duplex is not sufficient because stock GP4 copper reaches the TRRS contact.

For GP2/GP3, the legacy OLED/reversible peripheral solder jumpers are the default-open footprint. `J2.3` is directly connected to SCL, so the haptic module must not be populated on the right trackball build. Right OLED/haptic and the stock PAW3204 path are disabled for revision 1.

**Gate: passed.** See [`design/task2/TASK2B_RESULT.md`](design/task2/TASK2B_RESULT.md).

#### Task 2C — Lock the Kivipallur physical/electrical connector — NEXT

Audit the real Kivipallur source rather than assuming connector order.

Resolve:

- connector footprint and pitch
- physical side/orientation on the right PCB
- pin numbering as viewed from the KLOR PCB
- breakout mating orientation and service direction
- exact signal order: GND, 3V3, MOTION, SCK, MOSI, MISO, CS

**Gate:** connector footprint, orientation, pin numbering, and breakout mating direction are unambiguous.

#### Task 2D — Freeze the PCB net contract

Convert 2A–2C into an authoritative connector/net table.

Current proposal to verify:

| Breakout signal | Proposed KLOR right connection |
| --- | --- |
| GND | GND |
| 3.3 V | 3V3 |
| MOTION | NC for revision 1 |
| SCK | GP2 |
| MOSI | GP3 |
| MISO | GP4 |
| CS | GP9 |

**Gate:** every connector pin maps to one PCB net and MCU signal with no unresolved electrical ambiguity.

#### Task 2E — Freeze firmware ownership

Verify the trackball firmware variant against the stock QMK configuration.

Revision 1 should retain:

- GP1 = half-duplex split serial
- GP0 = RGB
- GP5/6/7/8 = matrix rows
- GP20/21/22/23/26/27 = matrix columns
- GP28/29 = encoder

Revision 1 disables:

- OLED / stock I2C use on GP2/GP3
- haptic
- audio on GP9
- stock PAW3204 path on GP2/GP3

**Gate:** firmware ownership agrees exactly with the electrical contract and contains no overlapping GPIO use.

#### Task 2F — Freeze the complete interface

Produce one authoritative table covering:

`connector pin → breakout signal → PCB net → MCU GPIO → firmware function → stock-circuit change`

Also record every required stock-circuit deletion, isolation, bypass, and intentionally unpopulated optional feature.

**Task 2 completion gate:** one unambiguous connector/pin/net/firmware contract exists and there is **zero unresolved GPIO or net ownership conflict**.

Do not begin production PCB routing before Task 2F passes.

### Task 3 — Create the right-hand trackball PCB derivative

Start from stock KLOR 1.4 but create a distinct right-hand trackball derivative.

Implement only changes authorized by Task 2, including:

- remove `SW22` and `D22`
- bypass RGB as `SW13 DOUT -> SW14 DIN`
- add the locked Kivipallur interface
- route GP2/GP3/GP4/GP9
- isolate `J1.3` from GP4 using the Task 2B-locked copper change
- retire conflicting I2C/PAW3204/audio loads according to Task 2
- add breakout pass-through / edge clearance
- preserve R32/R33 and right encoder

**Completion gate:** KiCad DRC passes except documented intentional exceptions; no unrouted PMW nets; RGB bypass continuity explicit; board-edge/cutout clearances pass; stock/reference PCB files remain unchanged.

### Task 4 — Modify the right Konrad switchplate

Use the STEP as mechanical source of truth. Remove the R34 opening as required, add Type-C mounts, local housing relief, and breakout pass-through while preserving unaffected switches and all verified structural mounting axes.

**Completion gate:** clean fit in the locked assembly and clean export to required CAD/fabrication formats.

### Task 5 — Create an editable right-case derivative and modify the case

Establish a reproducible editable workflow from the stock right-case STL, then make only local trackball-region changes. Task 1 already established that local stock-shell relief is required around the locked housing.

**Completion gate:** editable/reproducible, manifold, printable, serviceable, and fits the locked assembly without undocumented mesh-only hacks.

### Task 6 — Run complete mechanical + PCB validation

Assemble the final right PCB, switchplate, housing, ball, breakout, retained switches, encoder, and case. Recheck collisions, serviceability, key travel, fastener access, mounting coherence, and final DRC.

**Completion gate:** implemented mechanical and PCB fabrication geometry is frozen.

### Task 7 — Implement the QMK trackball firmware variant

Implement the 39-key Konrad trackball variant, asymmetric 20/19 RGB topology, PMW3360 interface from the final Task 2 contract, right-only pointing device, retained split/encoder, and disabled conflicting optional stock features.

Bring-up order: matrix → split → encoder → RGB → SPI → PMW3360 motion → pointer orientation/scaling.

**Completion gate:** firmware builds cleanly with no overlapping pin ownership.

### Task 8 — Fabrication package and hardware bring-up

Only after Tasks 1–7 pass: generate/review fab outputs, export final printed parts, prepare BOM/assembly notes, fabricate first revision, perform power/continuity checks, then bring up keyboard functions followed by PMW3360.

**Completion gate:** first-revision hardware passes electrical, mechanical, and firmware smoke tests; deviations are fed back before fabrication lock.

---

## Fabrication gate

Do **not** order the modified PCB or treat final printed parts as production-ready until Tasks 1–7 pass their completion gates.

Task 1 locks the **reference mechanical placement**. Task 2 locks the **electrical/firmware interface**. Tasks 3–7 implement and validate the final right-side hardware.
