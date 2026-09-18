# KLOR Trackball

## Goal

Modify the **right half** of **KLOR 1.4 MX** using the **Konrad** layout so it gains a **25 mm PMW3360 trackball** based on the Klorball35 / Kivipallur architecture, while preserving the stock KLOR design everywhere that does not conflict with the trackball.

The **left half remains stock**.

---

## Project status

| Task | Status | Result |
| --- | --- | --- |
| Task 1 — mechanical reference assembly | **COMPLETE** | trackball placement mechanically locked |
| Task 2 — electrical + firmware interface | **COMPLETE** | connector/net/GPIO/firmware contract locked |
| Task 3 — right-hand trackball PCB derivative | **IN PROGRESS** | 3A–3B complete; 3C PCB synchronization next |
| Task 4 — right Konrad switchplate | pending | — |
| Task 5 — editable right-case derivative | pending | — |
| Task 6 — complete mechanical + PCB validation | pending | — |
| Task 7 — QMK trackball variant | pending | — |
| Task 8 — fabrication + hardware bring-up | pending | — |

The project is **not fabrication-locked yet**. Tasks 1 and 2 provide the verified inputs for Task 3.

### Canonical documents

- **Task 1:** [`design/task1/README.md`](design/task1/README.md)
- **Task 2:** [`design/task2/README.md`](design/task2/README.md)
- **Task 3:** [`design/task3/README.md`](design/task3/README.md)
- Engineering handoff: [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md)
- Machine-readable geometry/electrical state: [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml)

Task-specific result files, audit scripts, manifests, and CI workflows live under `design/task1/`, `design/task2/`, and `.github/workflows/`.

---

## Implementation baseline

All new implementation work starts from **`main`**.

Reference sources remain unchanged:

- `klor1.4/` — stock KLOR 1.4 source/reference
- `klorball35/` — working trackball/reference architecture

Modified PCB, CAD, and firmware artifacts must be **trackball-specific derivatives** rather than silent replacements of the stock source files.

The historical branch `klor-trackball/konrad-trackball-implementation` is not part of the baseline.

---

## Locked design direction

### Keyboard

- Base: **KLOR 1.4 MX**
- Layout: **Konrad**
- Left half: stock
- Final key count: **39**
  - left: 20
  - right: 19
- Keep right rotary encoder
- Keep R32 and R33
- Remove logical key **R34**
  - PCB footprint: `SW22`
  - diode: `D22`
  - firmware matrix position: `[7,1]`
- Preserve all unaffected MX and south-facing SK6812 Mini-E positions

`R34` is a logical Konrad key position, not a KiCad resistor reference.

### Trackball stack

- Ball: **25 mm**
- Sensor: **PixArt PMW3360DM-T2QU**
- Breakout: **Kivipallur PMW3360**
- Housing: **kepeo Keyball 25mm Trackball Case Type C**, Thingiverse 6719828

The Type-C housing screws are a **housing-to-switchplate interface**, not main-PCB mounting holes.

---

## Task 1 locked mechanical inputs

Task 1 validated and froze the trackball reference assembly.

Canonical fabrication frame: **KLOR Gerber/Excellon XY**, millimetres.

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Housing screw 1 | **156.111** | **-126.768** |
| Housing screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout/pass-through center | **143.111** | **-134.748** |
| Deleted SW22 center | **143.025** | **-128.770** |

Important mechanical results:

- Type-C mounting plane = installed switchplate top
- 25 mm ball top = case `Z ≈ 38.2 mm`
- housing rim = case `Z ≈ 38.9 mm`
- all eight structural mounting axes remain clear
- retained switches, right encoder, MCU, and TRRS remain clear
- breakout insertion/service corridor is valid
- the stock right-case shell **does intersect the Type-C housing locally**

That case interference is an expected Task 5 shell-relief requirement. Do **not** move the locked trackball placement merely to avoid it.

For the complete mechanical audit, transforms, clearances, and source hashes, see [`design/task1/README.md`](design/task1/README.md).

---

## Task 2 locked electrical/firmware inputs

Task 2 audited the actual KiCad and QMK sources and froze the complete interface with **zero unresolved GPIO conflicts and zero unresolved net conflicts**.

For the complete 2A–2F narrative, evidence, and Task 3 handoff, see:

**[`design/task2/README.md`](design/task2/README.md)**

### Final PMW3360 connector contract

The KLOR keyboard-side connector is deliberately reversed relative to the opposite-facing Kivipallur breakout.

| KLOR pin | Kivipallur pin | Signal | Final PCB net | MCU |
| ---: | ---: | --- | --- | --- |
| 1 | 7 | CS | `PMW_CS` | GP9 |
| 2 | 6 | MISO | `PMW_MISO` | GP4 |
| 3 | 5 | MOSI | `PMW_MOSI` | GP3 |
| 4 | 4 | SCK | `PMW_SCK` | GP2 |
| 5 | 3 | MOTION | **NC** | — |
| 6 | 2 | +3V3 | `VCC` | U1.21 |
| 7 | 1 | GND | `GND` | ground |

Key locked requirements:

- remove `SW22` and `D22`
- preserve `col1` and `row3`; do not bridge them
- RGB bypass: `SW13 DOUT → SW14 DIN`
- preserve GP1 `TX → J1.4` half-duplex split transport
- physically isolate GP4 from TRRS `J1.3` using the Task 2B-verified copper edit
- GP2 = PMW3360 SCK
- GP3 = PMW3360 MOSI
- GP4 = PMW3360 MISO
- GP9 = PMW3360 CS
- Kivipallur `+3V3` connects to existing KLOR `VCC`
- MOTION remains unconnected for revision 1
- right OLED/haptic/audio/stock PAW3204 paths remain disabled/DNP for revision 1
- final RGB topology = **20 left / 19 right / 39 total**

### Firmware ownership

The later Task 7 firmware derivative is locked to:

```text
PMW3360 over SPI0

SCK  = GP2
MOSI = GP3
MISO = GP4
CS   = GP9

split serial = GP1, half-duplex
RGB          = GP0
handedness   = EE_HANDS
pointing side = right
MOTION       = unused
```

Detailed firmware configuration and disabled stock-feature ownership are documented in [`design/task2/README.md`](design/task2/README.md).

---

## Task 3 — create the right-hand trackball PCB derivative — IN PROGRESS

The detailed Task 3 plan is in **[`design/task3/README.md`](design/task3/README.md)**.

Task 3 is split into:

```text
3A derivative project
 ↓
3B schematic contract
 ↓
3C destructive PCB edits
 ↓
3D connector + fabricated pass-through
 ↓
3E PMW3360 routing
 ↓
3F preservation + DRC audit
 ↓
3G PCB freeze
```

### Current status

**3A — COMPLETE.**

A distinct schematic-driven derivative now exists at:

```text
PCB/konrad_trackball/
```

The derivative starts from an exact stock KLOR PCB/schematic/library baseline, uses the project basename `konrad_trackball`, and intentionally excludes stock Gerbers. The stock project under `klor1.4/PCB/klor1_4/` remains unchanged.

See [`design/task3/TASK3A_RESULT.md`](design/task3/TASK3A_RESULT.md).

**3B — COMPLETE.**

The derivative schematic now implements the frozen Task 2 contract:

- SW22 and D22 removed logically;
- direct `SW13 DOUT → SW14 DIN` RGB bypass;
- U1 ownership renamed to `PMW_SCK` / `PMW_MOSI` / `PMW_MISO` / `PMW_CS`;
- new J4 1×7 Kivipallur interface with keyboard-side order `CS, MISO, MOSI, SCK, NC, VCC, GND`;
- J1.3 explicitly NC while J1.4/TX remains the half-duplex split path;
- J2 haptic, OLED1, and BZ1 marked DNP for revision 1.

The derivative PCB is intentionally still byte-identical to stock at the end of 3B.

See [`design/task3/TASK3B_RESULT.md`](design/task3/TASK3B_RESULT.md).

**3C — NEXT:** synchronize the schematic contract onto the PCB and perform the authorized destructive physical edits.

Task 3 must continue to preserve the locked Task 1 mechanical placement and Task 2 electrical/firmware interface.

## Remaining roadmap

### Task 4 — right Konrad switchplate

Use the STEP source of truth. Add the Type-C housing mounting points, local housing relief, R34-region changes, and breakout pass-through while preserving unaffected openings and all verified structural mounting axes.

### Task 5 — editable right-case derivative

Establish a reproducible editable workflow from the stock right-case STL and provide the local shell relief proven necessary by Task 1.

### Task 6 — complete modified-assembly validation

Validate the actual modified PCB + switchplate + housing + breakout + retained keys + encoder + case as one assembly.

### Task 7 — QMK trackball variant

Implement the 39-key trackball-specific firmware, asymmetric RGB map, PMW3360 SPI interface, right-only pointing device, retained split/encoder, and disabled conflicting optional stock features.

### Task 8 — fabrication + hardware bring-up

Generate and independently review fabrication outputs, prepare assembly notes, fabricate the first revision, perform continuity/power checks, and bring up keyboard functions before PMW3360 motion.

---

## Fabrication gate

Do **not** order the modified PCB or treat final printed parts as production-ready until Tasks 3–7 pass their completion gates.

Task 1 locks the **mechanical reference placement**.

Task 2 locks the **electrical/firmware interface**.

Task 3 is the next implementation step.
