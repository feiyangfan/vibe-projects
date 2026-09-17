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

Task 1 is fully complete. All subtasks `1A → 1G` passed and the original candidate trackball placement is mechanically locked.

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
- composed PCB → right-case conservative propagated residual bound: **≤ 0.026082 mm**

Verified mechanical findings:

- Type-C housing mounting plane = switchplate top at case `Z = 7.7 mm`
- ball top = case `Z = 38.2 mm`
- housing rim ≈ case `Z = 38.9 mm`
- nearest retained keycap gap: `SW15` **2.654 mm**
- next retained keycap gap: `SW21` **3.444 mm**
- right encoder `SW18` clearance: **27.772 mm**
- MCU `U1` clearance: **40.321 mm**
- TRRS `J1` clearance: **46.460 mm**
- structural fastener collisions: **0 / 8**
- structural boss collisions: **0 / 8**
- breakout service corridor minimum retained-keycap clearance: approximately **8.000 mm**

The unmodified stock right-case shell **does intersect the Type-C housing locally**. This is an expected downstream case-relief requirement, not a placement failure: all eight structural mounting axes and all retained components remain clear. Do not move the locked trackball placement merely to avoid that local shell relief.

Task 1 result: **`placement_locked: true`**.

The overall keyboard is **not fabrication-locked**. Electrical, PCB, switchplate, case, firmware, and final integrated validation remain.

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
- Remove logical key **R34**, implemented on the PCB as `SW22`, matrix `[7,1]`
- Preserve all other unaffected MX and south-facing SK6812 Mini-E positions

`R34` is the logical Konrad key position; it is **not** a KiCad resistor reference.

### Trackball stack

- ball: 25 mm
- sensor: PixArt PMW3360DM-T2QU
- sensor breakout: Kivipallur PMW3360 breakout
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

All gates pass. See [`design/task1/README.md`](design/task1/README.md) for the detailed decomposition and evidence.

If the locked XY placement ever changes, rerun Task 1A–1G and update together:

- `design/task1/reference_assembly_manifest.yaml`
- `design/konrad_trackball_geometry.yaml`
- `docs/KONRAD_TRACKBALL_HANDOFF.md`

### Task 2 — Lock the electrical and firmware interface — IN PROGRESS

Task 2 converts the current electrical proposal into one source-backed implementation contract before production PCB editing begins.

Dependency chain:

`2A → 2B → 2C → 2D → 2E → 2F`

#### Task 2A — Audit the removed-key circuit — IN PROGRESS

Audit the stock KiCad schematic and PCB around logical key R34 / `SW22`.

Resolve from source:

- exact `SW22` switch pad/net connectivity
- exact `D22` matrix-diode connectivity
- whether `D22` is removed or may remain electrically harmless
- exact RGB device associated with the deleted key position
- RGB `DIN` and `DOUT` nets and immediate upstream/downstream chain neighbors
- exact permanent copper bypass required after deleting that RGB device
- nearby components/traces that materially constrain the trackball PCB derivative

**Gate:** there is one unambiguous source-backed disposition for `SW22`, `D22`, the associated RGB device, and its data-chain bypass.

Reproducible audit script:

`design/task2/audit_task2a_removed_key.py`

CI workflow:

`.github/workflows/klor-task2a-electrical-audit.yml`

#### Task 2B — Audit GPIO ownership and split/TRRS routing

Trace GP2, GP3, GP4, and GP9 through the actual schematic and PCB copper.

Resolve:

- every stock function currently attached to those GPIOs
- GP4's optional full-duplex TX/TRRS route
- the exact copper segment/pad/via that must be isolated for GP4 to become PMW3360 MISO
- confirmation that GP1 remains the active half-duplex split serial path
- confirmation that retained matrix/RGB/encoder pins are unaffected

**Gate:** every proposed PMW GPIO has one owner and every conflicting stock electrical path has an explicit disposition.

#### Task 2C — Lock the Kivipallur physical/electrical connector

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

Current proposal to verify, not yet the final contract:

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

Verify the trackball firmware variant against the actual stock QMK configuration.

Revision 1 should retain:

- GP1 = half-duplex split serial
- GP0 = RGB
- GP5/6/7/8 = matrix rows
- GP20/21/22/23/26/27 = matrix columns
- GP28/29 = encoder

Revision 1 is expected to disable on the right trackball build:

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

Start from the stock KLOR 1.4 PCB but create a distinct right-hand trackball derivative.

Implement only the changes authorized by Task 2:

- remove R34 / `SW22`
- remove its RGB device and permanently bypass the LED chain in copper
- remove or retain `D22` exactly as Task 2A specifies
- add the locked Kivipallur connector/interface
- route GP2/GP3/GP4/GP9
- physically isolate GP4 from the optional full-duplex TRRS TX route
- add breakout pass-through / edge clearance
- alter the PCB outline only where required
- preserve R32/R33 and the right encoder

**Completion gate:** KiCad DRC passes except documented intentional exceptions; no unrouted PMW nets remain; RGB bypass continuity is explicit; board-edge/cutout clearances pass; stock/reference PCB files remain unchanged.

### Task 4 — Modify the right Konrad switchplate

Use the STEP as the mechanical source of truth.

Implement:

- remove the R34 switch opening as required
- add the two Type-C housing mounting locations from actual housing CAD
- add local outer relief for the housing
- add breakout pass-through / edge relief
- preserve unaffected switch openings and all verified structural mounting axes

**Completion gate:** modified switchplate fits the locked reference assembly without interference and exports cleanly to STEP/STL plus required fabrication formats.

### Task 5 — Create an editable right-case derivative and modify the case

Establish a reproducible editable workflow from the stock right-case STL, then make only local trackball-region changes.

Task 1 already established that local stock-shell relief is required around the locked housing.

Check housing/ball access, switchplate seating, breakout service access, retained keys, encoder, MCU/TRRS, structural mounts, wall thickness, printability, and assembly sequence.

**Completion gate:** the right-case derivative is editable/reproducible, manifold for printing, and fits the locked assembly without undocumented mesh-only hacks.

### Task 6 — Run the complete mechanical + PCB validation pass

Assemble the final right PCB, switchplate, housing, ball, breakout, retained switches, encoder, and case.

Verify no unresolved 3D collision, no trapped connector/breakout, acceptable key travel/clearance, fastener access, coherent mounting, and final PCB DRC after mechanically driven changes.

**Completion gate:** implemented mechanical and PCB fabrication geometry is frozen.

### Task 7 — Implement the QMK trackball firmware variant

Create a trackball-specific Konrad variant rather than mutating stock firmware into a mixed-purpose configuration.

Implement and verify:

- 39-key matrix/keymap with R34 absent
- asymmetric RGB: 20 left / 19 right / 39 total
- trackball-specific `g_led_config`
- PMW3360 SPI0 according to locked Task 2 contract
- right-half-only pointing device
- half-duplex split retained
- right encoder retained
- conflicting optional stock features disabled

Bring-up order: matrix → split → encoder → RGB → SPI → PMW3360 motion → pointer orientation/scaling.

**Completion gate:** firmware builds cleanly and contains no overlapping pin ownership.

### Task 8 — Fabrication package and hardware bring-up

Only after Tasks 1–7 pass:

- regenerate Gerbers/drills from the modified right PCB
- independently review fabrication outputs
- export final printable case/switchplate files
- prepare BOM/assembly notes
- fabricate/print first revision
- continuity/power checks before MCU/sensor installation
- keyboard bring-up first, then PMW3360

**Completion gate:** first-revision hardware passes electrical, mechanical, and firmware smoke tests; deviations are fed back into the handoff/YAML before fabrication lock.

---

## Fabrication gate

Do **not** order the modified PCB or treat final printed parts as production-ready until Tasks 1–7 pass their completion gates.

Task 1 locks the **reference mechanical placement**. Tasks 2–7 still have to implement and validate the final right-side hardware.