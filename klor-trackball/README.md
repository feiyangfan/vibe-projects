# KLOR Trackball

## Goal

Modify the **right half** of **KLOR 1.4 MX** using the **Konrad** layout so it gains a 25 mm PMW3360 trackball based on the Klorball35 / Kivipallur architecture, while preserving the stock KLOR design everywhere that does not conflict with the trackball.

The **left half remains stock**.

## Implementation baseline

All planning and future implementation should start from `main`.

The existing branch `klor-trackball/konrad-trackball-implementation` is **not part of the baseline** and should be ignored unless it is explicitly re-evaluated later. Do not copy design decisions from it into new work by default.

Reference sources that should remain unchanged:

- `klor1.4/` — stock KLOR 1.4 source/reference
- `klorball35/` — working trackball/reference architecture

New modified PCB, CAD, and firmware artifacts should be treated as **trackball-specific derivatives**, rather than silently replacing the stock reference files.

## Current status

The Type-C housing CAD has been obtained and measured, and a candidate XY placement has been defined. The design is **not fabrication-locked**.

Canonical design references:

- [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md) — detailed electrical/mechanical research and current design state
- [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml) — machine-readable geometry and pin assignments

The next phase is implementation, but it should be done in dependency order rather than as one large PCB/CAD/firmware change.

## Problems that must be solved first

### 1. The candidate trackball placement is not yet proven as a complete assembly

The current placement is based on measured housing geometry and 2D/AABB checks. It has **not** yet been validated in a complete 3D assembly containing:

- right PCB
- Konrad switchplate
- Type-C trackball housing
- Kivipallur breakout
- R32/R33 switches and keycaps
- right encoder
- MCU/TRRS region
- right case

Therefore the placement is a working baseline, not a production datum. PCB and case edits should not be finalized until the assembled interference check passes.

### 2. The stock KLOR PCB is a symmetric/reversible design, but this project needs a right-only derivative

KLOR 1.4 intentionally uses a symmetric front/back PCB architecture. This project keeps the left half stock while changing only the right half.

Do **not** convert the stock `klor1_4.kicad_pcb` into a universal trackball board. Create a right-hand trackball PCB derivative and preserve the stock board as the left/reference design.

### 3. The right case does not have a clean editable solid source in this repository

The Konrad switchplate has STEP/DXF/STL sources, but the regular right case is available here as STL only:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

Before doing detailed case work, establish an editable CAD workflow for the right case. Do not make the final case a chain of undocumented mesh edits.

### 4. The PCB electrical plan still needs a source-level audit

The proposed PMW3360 interface is:

| Breakout signal | KLOR right connection |
| --- | --- |
| GND | GND |
| 3.3 V | 3V3 |
| MOTION | NC initially |
| SCK | GP2 |
| MOSI | GP3 |
| MISO | GP4 |
| CS | GP9 |

Before routing, verify in the actual right-side copper/schematic:

- exact R34 / SW22 / RGB / D22 connectivity
- which nearby passives and traces collide with the breakout corridor
- the GP4 connection to the optional full-duplex TRRS TX path and exactly where it will be isolated
- connector pin order and physical orientation relative to the Kivipallur breakout
- breakout slot/edge-cut geometry and clearances

### 5. The stock firmware conflicts with the intended PMW3360 configuration

The stock QMK source currently uses or declares the same pins/features that the PMW3360 needs:

- GP2 / GP3 are configured for I2C and the stock PAW3204 path
- GP9 is configured for audio
- OLED, haptic, and audio are enabled in the stock keyboard metadata
- pointing-device support is disabled in the stock keyboard metadata
- the stock RGB configuration still assumes the original symmetric LED topology; the Konrad-specific `g_led_config` is not the active configuration in `klor.c`

The trackball build therefore needs an explicit firmware variant. It is not sufficient to add a PMW3360 driver while leaving the stock feature configuration untouched.

### 6. Fabrication acceptance criteria are not yet explicit enough

“Run DRC” and “check collisions” are necessary but not sufficient. Each implementation stage below has a concrete completion gate so that later work does not build on an unverified assumption.

---

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

Important measured Type-C values:

- ball center = CAD origin
- housing envelope ≈ **37.595 × 29.998 × 31.200 mm**
- housing/switchplate mounting plane ≈ **18 mm below ball center**
- top of a real 25 mm ball = **30.5 mm above the mounting plane**
- mounting screw pair = **15.96 mm measured / 16 mm nominal**
- screw-pair midpoint ≈ **6.212 mm toward the sensor side from ball center**

Exact source hashes and coordinates are recorded in the handoff and YAML.

### Working placement

KLOR native PCB/Gerber coordinates, millimetres:

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Screw 1 | **156.111** | **-126.768** |
| Screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |

The Type-C housing screws belong to the **switchplate/housing interface**, not automatically to the main PCB. The main PCB needs the Kivipallur breakout clearance/pass-through and electrical interface.

---

## Sequential implementation plan

Do these tasks in order. A later task should not start from an unverified output of an earlier task.

### Task 1 — Build and lock the mechanical reference assembly

Create a single reference assembly using the current placement and the stock/reference models.

Include at minimum:

- stock right KLOR PCB geometry
- Konrad switchplate STEP
- stock right Konrad case STL
- Type-C housing STEP
- 25 mm ball envelope
- Kivipallur breakout geometry
- R32/R33 switch + keycap envelopes
- right encoder envelope
- MCU/TRRS keepout envelopes

Check the candidate placement in full 3D and only move it when a concrete collision or assembly constraint requires it.

**Completion gate:**

- no unresolved collision with R32/R33, encoder, MCU/TRRS, or case-critical geometry
- ball exposure and housing mounting plane are understood
- breakout orientation and insertion/service path are understood
- final placement datums are written back to both the handoff and YAML if changed

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

**Completion gate:** there is one unambiguous connector/pin/net table and no unresolved GPIO ownership conflict.

### Task 3 — Create the right-hand trackball PCB derivative

Start from the stock KLOR 1.4 PCB but create a distinct right-hand trackball derivative.

Implement:

- remove R34 / SW22
- remove its RGB device and permanently bypass the LED chain in copper
- remove/relocate D22 or other parts only where the audited geometry requires it
- add the Kivipallur 7-pin connector/interface
- route GP2/GP3/GP4/GP9
- physically isolate GP4 from the optional full-duplex TRRS TX route
- add the breakout pass-through / edge clearance
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

- delete the R34 switch opening as required by the final assembly
- two Type-C housing mounting locations using the actual housing CAD
- local outer relief for the housing
- breakout pass-through / edge relief
- preserve unaffected switch openings and mounting features

**Completion gate:** modified switchplate fits the locked reference assembly with no interference and exports cleanly to STEP/STL plus the needed fabrication format.

### Task 5 — Create an editable right-case derivative and modify the case

First establish the case source workflow because the repository only contains the regular right case as STL.

Then make only local changes around the trackball assembly.

Check:

- housing shell clearance
- ball access
- switchplate seating/contact plane
- breakout/header/cable service access
- R32/R33 clearance
- encoder clearance
- MCU/TRRS clearance
- wall thickness
- printability and assembly sequence

**Completion gate:** the right-case derivative is editable/reproducible, manifold for printing, and fits the locked assembly without hidden mesh-only hacks.

### Task 6 — Run the complete mechanical + PCB validation pass

Assemble the final right-side PCB + switchplate + housing + ball + breakout + retained switches + encoder + case.

Verify:

- no 3D collisions
- no trapped/unserviceable connector or breakout
- acceptable keycap-to-housing clearance through full key travel
- acceptable case wall thickness and fastener access
- PCB/switchplate/case mounting remains coherent
- final PCB DRC still passes after any mechanically driven PCB changes

**Completion gate:** the mechanical placement and right-side fabrication geometry are frozen.

### Task 7 — Implement the QMK trackball firmware variant

Do not mutate the stock firmware configuration into a mixed-purpose configuration. Create a trackball-specific Konrad variant.

Implement and verify:

- Konrad 39-key matrix/keymap behavior with R34 absent
- asymmetric RGB topology: 20 left / 19 right / 39 total
- trackball-specific `g_led_config`
- PMW3360 on SPI0 using GP2/GP3/GP4 and CS=GP9
- right-half-only pointing device configuration
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

**Completion gate:** firmware builds cleanly and the configuration contains no overlapping pin ownership.

### Task 8 — Fabrication package and hardware bring-up

Only after Tasks 1–7 are complete:

- regenerate Gerbers/drills from the modified right PCB
- review fab outputs independently from KiCad source
- export final printable case and switchplate files
- prepare BOM/assembly notes for the trackball-specific right half
- fabricate/print a first revision
- perform continuity/power checks before installing the MCU/sensor
- bring up keyboard functions first, then PMW3360

**Completion gate:** first-revision hardware passes electrical, mechanical, and firmware smoke tests; any deviations are fed back into the handoff/YAML before declaring the design fabrication-locked.

---

## Fabrication gate

Do **not** order the modified PCB or treat the final printed parts as production-ready until Tasks 1–7 pass their completion gates.

If the working trackball placement changes, update both:

- [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md)
- [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml)

in the same commit.
