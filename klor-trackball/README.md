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

## Current status

**Task 1 — mechanical reference assembly is complete and the trackball placement is mechanically locked.**

The successful Task 1 audit verified the checked-in Type-C sources, solved the PCB/switchplate/case coordinate relationships, reconstructed the stock stack-up, checked retained components and structural mounts, verified the breakout service corridor, and confirmed that the original placement does not need to move.

The overall project is **not fabrication-locked**. Electrical/PCB/CAD/firmware implementation and final integrated validation remain.

Canonical references:

- [`design/task1/TASK1_RESULT.md`](design/task1/TASK1_RESULT.md) — Task 1 engineering result
- [`design/task1/reference_assembly_manifest.yaml`](design/task1/reference_assembly_manifest.yaml) — machine-readable mechanical source of truth
- [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md) — consolidated engineering handoff
- [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml) — machine-readable project geometry and pin assignments

## Locked design direction

### Keyboard

- Base: **KLOR 1.4 MX**
- Layout: **Konrad**
- Left half: stock
- Final target: **39 keys** = 20 left + 19 right
- Keep right encoder
- Keep R32 and R33
- Remove **R34 / SW22 / matrix `[7,1]`** for the trackball
- Preserve all other unaffected MX and south-facing SK6812 Mini-E positions

### Trackball stack

- 25 mm ball
- PixArt PMW3360DM-T2QU
- Kivipallur PMW3360 breakout
- kepeo **Keyball 25mm Trackball Case Type C**, Thingiverse 6719828

Important Type-C values:

- ball center = CAD origin
- housing envelope ≈ **37.595 × 29.998 × 31.200 mm**
- housing/switchplate mounting plane ≈ **18 mm below ball center**
- real 25 mm ball top = **30.5 mm above the mounting plane**
- mounting screw pair = **15.96 mm measured / 16 mm nominal**
- screw-pair midpoint ≈ **6.212 mm toward the sensor side from ball center**

### Locked mechanical placement

Canonical frame: **KLOR Gerber/Excellon fabrication XY**, millimetres.

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Screw 1 | **156.111** | **-126.768** |
| Screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |
| Deleted SW22 center | **143.025** | **-128.770** |

The Type-C housing screws belong to the **switchplate/housing interface**, not the main PCB. The main PCB needs Kivipallur breakout clearance/pass-through plus its electrical interface.

---

## Sequential implementation plan

Do the tasks in dependency order. A later task must not build on an unverified output of an earlier task.

### Task 1 — Build and lock the mechanical reference assembly

Task 1 is decomposed into smaller gates so future changes can be revalidated without treating the entire mechanical problem as one opaque step.

Dependency chain:

`1A → 1B → 1C → 1D → 1E → 1F → 1G`

The original Task 1 audit was completed before this decomposition was introduced, so the existing verified evidence maps onto all seven subtasks. The split below is now the required structure for future reruns or placement changes.

#### Task 1A — Lock source geometry — COMPLETE

Verify and identify every mechanical input:

- exact Type-C STEP and both source STL hashes
- original ZIP provenance
- stock KLOR PCB and NPTH drill/frame reference
- Konrad switchplate source
- stock right-case STL
- Kivipallur breakout source

**Gate:** every mechanical input is reproducible, checked in, and unambiguously identified.

The current source set passes this gate.

#### Task 1B — Establish the common coordinate frame — COMPLETE

Derive and validate rigid transforms using multiple physical features rather than screenshots, bounding-box alignment, or a single datum:

- KiCad PCB → Gerber/Excellon fabrication frame
- KiCad PCB → native Konrad switchplate frame
- native switchplate → native right-case frame
- composed KiCad PCB → native right-case frame

Record the transform matrices, translations, matched feature counts, and fit residuals.

**Gate:** PCB, switchplate, and case can be overlaid reproducibly in one coordinate system with quantified alignment error.

Current verified evidence:

- KiCad → Gerber: 21 matched MX centers, RMS **0.000181 mm**
- KiCad → switchplate: 18 matched MX openings, RMS **0.020019 mm**
- switchplate → case: 8 structural mounting axes, RMS **0.006063 mm**
- explicit composed PCB → case transform is recorded in the Task 1 manifest and [`design/task1/TASK1B_RESULT.md`](design/task1/TASK1B_RESULT.md)

#### Task 1C — Place the trackball housing — COMPLETE

- apply the locked XY ball/screw placement
- resolve housing Z from the real switchplate mounting plane
- include the 25 mm ball
- verify mounting-plane relationship and ball exposure

**Gate:** housing placement is fully defined in XYZ and independently reproducible.

#### Task 1D — Place the breakout and service path — COMPLETE

- use the real Kivipallur breakout geometry
- position it relative to the housing/sensor
- verify pass-through direction
- verify insertion/removal and service access

**Gate:** breakout orientation and service path are physically plausible and documented.

#### Task 1E — Add retained-component keepouts — COMPLETE

Include collision bodies/envelopes for:

- R32/R33 retained switch/keycap region
- right encoder
- MCU region
- TRRS region
- structural mounting axes/fasteners
- any other nearby fixed geometry that constrains the trackball

**Gate:** every required retained component has a usable collision representation.

#### Task 1F — Run collision and clearance audit — COMPLETE

Check and record explicit pass/fail evidence for:

- housing ↔ retained thumb keys
- housing ↔ encoder
- housing/breakout ↔ MCU/TRRS
- housing ↔ structural mounts
- housing ↔ stock right-case shell
- ball access/exposure
- breakout serviceability

Record minimum clearances where meaningful.

**Gate:** every required collision/service check has an explicit result. Local stock-case shell interference is permitted only when structural mounts remain clear and the later case task has a defined local-relief requirement.

#### Task 1G — Freeze or revise placement — COMPLETE

If 1F passes, freeze the placement. If it fails, change only the minimum necessary placement parameter and rerun every affected upstream/downstream check.

If XY ever changes, update together:

- `design/task1/reference_assembly_manifest.yaml`
- `design/konrad_trackball_geometry.yaml`
- `docs/KONRAD_TRACKBALL_HANDOFF.md`

**Gate:** one justified mechanical placement is locked as the input to Tasks 2–5.

Current result: **`placement_locked: true`**. Do not move the trackball merely to avoid the documented local stock-case shell relief.

### Task 2 — Lock the electrical and firmware interface

Audit the stock schematic/PCB and convert the current pin proposal into an exact implementation contract.

Resolve:

- R34/SW22 matrix and diode removal details
- deleted RGB device and exact copper bypass
- D22 and neighboring component/trace disposition
- GP4/full-duplex TRRS isolation point
- Kivipallur connector footprint, pin order, side, and orientation
- GP2/GP3/GP4/GP9 routing targets
- which stock optional features are disabled in the trackball firmware variant

Firmware contract for revision 1 should keep:

- GP1 = half-duplex split serial
- GP0 = RGB
- GP5/6/7/8 = rows
- GP20/21/22/23/26/27 = columns
- GP28/29 = encoder

Revision 1 should disable on the right-side trackball build:

- OLED
- haptic
- audio
- stock PAW3204 path

**Completion gate:** one unambiguous connector/pin/net table exists and there is no unresolved GPIO ownership conflict.

### Task 3 — Create the right-hand trackball PCB derivative

Start from the stock KLOR 1.4 PCB but create a distinct right-hand trackball derivative.

Implement:

- remove R34 / SW22
- remove its RGB device and permanently bypass the LED chain in copper
- remove/relocate D22 or other parts only where the audited geometry requires it
- add the Kivipallur 7-pin connector/interface
- route GP2/GP3/GP4/GP9
- physically isolate GP4 from the optional full-duplex TRRS TX route
- add breakout pass-through / edge clearance
- alter the PCB outline only where required
- preserve R32/R33 and the right encoder

**Completion gate:**

- KiCad DRC passes except for documented intentional exceptions
- no unrouted PMW3360 nets
- RGB bypass continuity is explicit
- board edge/cutout clearances pass
- left/reference stock PCB files remain unchanged

### Task 4 — Modify the right Konrad switchplate

Use the STEP as the mechanical source of truth.

Implement:

- delete the R34 switch opening as required
- add the two Type-C housing mounting locations from actual housing CAD
- add local outer relief for the housing
- add breakout pass-through / edge relief
- preserve unaffected switch openings and all verified structural mounting axes

**Completion gate:** modified switchplate fits the locked reference assembly without interference and exports cleanly to STEP/STL plus required fabrication formats.

### Task 5 — Create an editable right-case derivative and modify the case

The repository contains the regular right case as STL only. Establish a reproducible editable workflow, then make only local trackball-region changes.

Check:

- housing shell clearance
- ball access
- switchplate seating/contact plane
- breakout/header/cable service access
- R32/R33 clearance
- encoder clearance
- MCU/TRRS clearance
- preservation of the eight verified structural mounting axes
- wall thickness
- printability and assembly sequence

Task 1 established that the stock shell requires local relief around the housing; this is expected and must not be solved by moving the locked placement.

**Completion gate:** the right-case derivative is editable/reproducible, manifold for printing, and fits the locked assembly without undocumented mesh-only hacks.

### Task 6 — Run the complete mechanical + PCB validation pass

Assemble the final right-side PCB + switchplate + housing + ball + breakout + retained switches + encoder + case.

Verify:

- no unresolved 3D collisions
- no trapped/unserviceable connector or breakout
- acceptable keycap-to-housing clearance through full key travel
- acceptable case wall thickness and fastener access
- PCB/switchplate/case mounting remains coherent
- final PCB DRC still passes after mechanically driven PCB changes

**Completion gate:** the implemented mechanical and PCB fabrication geometry is frozen.

### Task 7 — Implement the QMK trackball firmware variant

Create a trackball-specific Konrad variant rather than mutating the stock firmware into a mixed-purpose configuration.

Implement and verify:

- Konrad 39-key matrix/keymap behavior with R34 absent
- asymmetric RGB topology: 20 left / 19 right / 39 total
- trackball-specific `g_led_config`
- PMW3360 on SPI0 using GP2/GP3/GP4 and CS=GP9
- right-half-only pointing-device configuration
- half-duplex split on GP1
- right encoder retained
- OLED/haptic/audio/PAW3204 disabled for the initial trackball variant

Bring-up order:

1. matrix
2. split transport
3. encoder
4. RGB chain/map
5. SPI communication
6. PMW3360 motion
7. pointer orientation/scaling

**Completion gate:** firmware builds cleanly and contains no overlapping pin ownership.

### Task 8 — Fabrication package and hardware bring-up

Only after Tasks 1–7 pass:

- regenerate Gerbers/drills from the modified right PCB
- review fabrication outputs independently from KiCad source
- export final printable case and switchplate files
- prepare BOM/assembly notes for the trackball-specific right half
- fabricate/print a first revision
- perform continuity/power checks before installing MCU/sensor
- bring up keyboard functions first, then PMW3360

**Completion gate:** first-revision hardware passes electrical, mechanical, and firmware smoke tests; deviations are fed back into the handoff/YAML before declaring the design fabrication-locked.

---

## Fabrication gate

Do **not** order the modified PCB or treat final printed parts as production-ready until Tasks 1–7 pass their completion gates.

Task 1 locks the **reference placement**, not the finished fabrication geometry. Tasks 2–7 still have to implement and validate the derivative hardware.