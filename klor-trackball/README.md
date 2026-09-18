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
- **2C complete** — Kivipallur connector footprint, pin order, mating handedness, and service orientation locked
- **2D complete** — connector-to-PCB-net/MCU contract frozen
- **2E complete** — QMK firmware ownership and peripheral contract frozen
- **2F next** — complete interface freeze

Canonical Task 2 files:

- [`design/task2/TASK2A_RESULT.md`](design/task2/TASK2A_RESULT.md)
- [`design/task2/TASK2B_RESULT.md`](design/task2/TASK2B_RESULT.md)
- [`design/task2/TASK2C_RESULT.md`](design/task2/TASK2C_RESULT.md)
- [`design/task2/TASK2D_RESULT.md`](design/task2/TASK2D_RESULT.md)
- [`design/task2/TASK2E_RESULT.md`](design/task2/TASK2E_RESULT.md)
- [`design/task2/task2_manifest.yaml`](design/task2/task2_manifest.yaml)
- `design/task2/audit_task2a_removed_key.py`
- `design/task2/audit_task2b_gpio_trrs.py`
- `design/task2/audit_task2c_kivipallur_connector.py`
- `design/task2/audit_task2d_pcb_net_contract.py`
- `design/task2/audit_task2e_firmware_ownership.py`
- `.github/workflows/klor-task2a-electrical-audit.yml`
- `.github/workflows/klor-task2b-gpio-trrs-audit.yml`
- `.github/workflows/klor-task2c-kivipallur-connector-audit.yml`
- `.github/workflows/klor-task2d-pcb-net-contract-audit.yml`
- `.github/workflows/klor-task2e-firmware-ownership-audit.yml`

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

#### Task 2C — Lock the Kivipallur physical/electrical connector — COMPLETE

The Kivipallur breakout uses a **1 × 7, 2.54 mm through-hole vertical header** (`J1`) on `B.Cu`. Its exact source pin order is:

```text
1 GND
2 3V3
3 MOTION
4 SCK
5 MOSI
6 MISO
7 CS
```

The working Klorball35 right PCB uses the same footprint as keyboard-side `J2` on `F.Cu`, but deliberately reverses the physical order:

```text
1 CS
2 MISO
3 MOSI
4 SCK
5 NC
6 3V3
7 GND
```

The connectors mate opposite-facing as `breakout pin N <-> keyboard pin (8-N)`, so the signals line up directly. Breakout MOTION pin 3 therefore lands on keyboard pin 5, which is intentionally NC for revision 1.

The Klorball35 `2 × 22 mm` breakout rectangle is a `Cmts.User` mechanical guide, **not a fabricated Edge.Cuts slot**. Its keyboard header is parallel to the 22 mm axis and offset from the guide center by **4.613622 mm**. Task 3 must create the actual KLOR pass-through/edge clearance at the Task 1-locked breakout datum.

KLOR target orientation is now locked against the canonical Gerber frame:

- keyboard connector side: `F.Cu`
- row axis: global Y, parallel to the 22 mm guide
- header side of guide: positive X / non-sensor side
- breakout service direction: negative X
- pin 1: negative-Y end
- pin 7: positive-Y end
- physical row from negative Y to positive Y: `CS, MISO, MOSI, SCK, NC, 3V3, GND`

Task 3 may resolve final production XY against the locked assembly, but it may not flip connector side, row handedness, numbering, or the `N <-> 8-N` mating rule without reopening Task 2C.

**Gate: passed.** See [`design/task2/TASK2C_RESULT.md`](design/task2/TASK2C_RESULT.md).

#### Task 2D — Freeze the PCB net contract — COMPLETE

Task 2D composes the Task 2B GPIO ownership with the Task 2C-fixed physical connector order.

Locked derivative contract:

| KLOR pin | Breakout signal | Target PCB net | MCU / U1 pad | Stock source net |
| ---: | --- | --- | --- | --- |
| 1 | CS | `PMW_CS` | GP9 / U1.12 | `AUDIO` |
| 2 | MISO | `PMW_MISO` | GP4 / U1.7 | `RX` |
| 3 | MOSI | `PMW_MOSI` | GP3 / U1.6 | `SCL` |
| 4 | SCK | `PMW_SCK` | GP2 / U1.5 | `SDA` |
| 5 | MOTION | **NC** | none | none |
| 6 | +3V3 | `VCC` | U1.21 / VCC rail | `VCC` |
| 7 | GND | `GND` | U1 ground rail | `GND` |

Important source correction: stock KLOR calls the controller supply rail **`VCC`**, not `3V3`. With the selected Elite-Pi this is the 3.3 V controller rail, so Kivipallur `+3V3` connects to the existing KLOR `VCC` net. Task 3 must not create a separate KLOR `3V3` rail merely to mirror the breakout label.

The four reassigned signal nets are frozen as `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, and `PMW_SCK`. `AUDIO`, `RX`, `SCL`, and `SDA` remain useful only as names for the stock-source topology being replaced.

Task 3 must still implement all Task 2B dispositions: J1.3 physical isolation for GP4, audio disabled/BZ1 inactive for GP9, I2C/PAW3204 disabled on GP2/GP3, J2 haptic DNP, and legacy I2C jumpers open.

**Gate: passed.** See [`design/task2/TASK2D_RESULT.md`](design/task2/TASK2D_RESULT.md).

#### Task 2E — Freeze firmware ownership — COMPLETE

The trackball firmware must be a separate derivative of the stock KLOR QMK source.

Locked revision-1 GPIO ownership:

| GPIO | Firmware owner |
| --- | --- |
| GP0 | WS2812 / RGB matrix |
| GP1 | half-duplex split serial |
| GP2 | PMW3360 SCK |
| GP3 | PMW3360 MOSI |
| GP4 | PMW3360 MISO |
| GP5/6/7/8 | matrix rows |
| GP9 | PMW3360 CS |
| GP20/21/22/23/26/27 | matrix columns |
| GP28/29 | encoder |

The QMK trackball path is locked to PMW3360 over SPI0:

```text
POINTING_DEVICE_ENABLE = yes
POINTING_DEVICE_DRIVER = pmw3360
SPI_DRIVER = SPID0
SPI_SCK_PIN = GP2
SPI_MOSI_PIN = GP3
SPI_MISO_PIN = GP4
PMW33XX_CS_PIN = GP9
SPLIT_POINTING_ENABLE
POINTING_DEVICE_RIGHT
EE_HANDS
```

MOTION remains unused, so revision 1 must not define `POINTING_DEVICE_MOTION_PIN`.

The stock source has several conflicts that the trackball variant must retire:

- `I2C1_SDA_PIN GP2` / `I2C1_SCL_PIN GP3`
- PAW3204 SDIO/SCLK on GP2/GP3
- optional full-duplex serial TX on GP4
- `AUDIO_PIN GP9`
- I2C1 and audio PWM peripheral ownership

The stock default **and** Vial keymap `rules.mk` files also explicitly re-enable OLED, audio, music, and haptics. Therefore neither rules file may be reused unchanged for the trackball build.

Revision 1 feature state:

- pointing device: enabled
- RGB matrix: enabled
- encoder: enabled
- split serial: enabled, half duplex
- OLED: disabled
- haptic: disabled
- audio/music: disabled
- stock PAW3204: disabled
- I2C1: disabled
- audio PWM4: disabled

SPI remains enabled with `HAL_USE_SPI TRUE` and `RP_SPI_USE_SPI0 TRUE`. The trackball variant disables unused I2C1 and PWM4 ownership.

Pointer rotation/inversion, CPI, lift-off distance, scrolling, acceleration, and auto-mouse behavior remain Task 7 bring-up/tuning work. The revision-1 baseline leaves auto-mouse disabled until raw PMW3360 motion is verified.

RGB ownership remains GP0 with the already-locked 20-left / 19-right / 39-total topology; detailed `g_led_config` implementation remains Task 7.

**Gate: passed.** See [`design/task2/TASK2E_RESULT.md`](design/task2/TASK2E_RESULT.md).

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
