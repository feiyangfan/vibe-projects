# KLOR 1.4 MX + 25 mm Trackball — Konrad Engineering Handoff

## Purpose

This is the canonical engineering handoff for the KLOR trackball modification.

Target: **KLOR 1.4 MX, Konrad layout**, with a **25 mm PMW3360 trackball on the right half** using the Klorball35/Kivipallur architecture. The left half remains stock.

## Current implementation status

**Task 1 — mechanical reference assembly: COMPLETE.**

The candidate trackball placement has been validated against the checked-in PCB, Konrad switchplate, right-case STL, Type-C housing geometry, retained keys, encoder, MCU/TRRS regions, structural mounting axes, and Kivipallur breakout service corridor.

The placement did **not** need to move and is now mechanically locked.

Canonical Task 1 evidence:

- [`../design/task1/TASK1_RESULT.md`](../design/task1/TASK1_RESULT.md)
- [`../design/task1/reference_assembly_manifest.yaml`](../design/task1/reference_assembly_manifest.yaml)
- CI workflow: `.github/workflows/klor-task1-mechanical-audit.yml`

**Task 2 — electrical and firmware interface: COMPLETE.** Task 2F passed with zero unresolved GPIO/net conflicts.

**Task 3 — right-hand trackball PCB derivative: IN PROGRESS. Tasks 3A–3E are COMPLETE.** J4 and the fabricated pass-through are mechanically fixed, and the four PMW signals plus VCC/GND are routed. MOTION remains NC. **Next: Task 3F — preservation and integrated KiCad DRC audit.**

The overall design is **not fabrication-locked** yet. Mechanical placement is locked; PCB/CAD/firmware implementation and final integrated validation remain.

---

## Locked keyboard direction

- Base PCB: `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- Layout: **Konrad**
- Switch type: **MX**
- Left half: stock
- Final key count: **39**
  - left: 20
  - right: 19
- Right rotary encoder: retain
- Right thumb keys:
  - R32: retain
  - R33: retain
  - R34 / PCB switch `SW22` / matrix `[7,1]`: remove for trackball
- Preserve all unaffected MX and south-facing SK6812 Mini-E positions.

Do not move retained thumb keys merely to avoid local case/switchplate modification; Task 1 demonstrated adequate clearance at the locked placement.

---

## Trackball stack

Use the external Klorball35-style sensor assembly rather than integrating the PMW3360 support circuit directly onto the KLOR PCB.

- Ball: 25 mm
- Sensor: PixArt PMW3360DM-T2QU
- Sensor breakout: Kivipallur PMW3360 breakout
- Housing: kepeo **Keyball 25mm Trackball Case Type C**, Thingiverse 6719828

Checked-in source directory:

`Keyball 25mm Trackball Case Type C - 6719828/`

Primary files:

- `files/keyball_trackball_case_25mm_type_c.stp`
- `files/keyball_trackball_case_25mm_type_c_left.stl`
- `files/keyball_trackball_case_25mm_type_c_right.stl`

Exact verified hashes:

| File | SHA-256 |
| --- | --- |
| ZIP archive | `ad2ee79388c01fcb775ee08e35761d14b27fbd53ecffabfbdc45add77830e206` |
| Type-C STEP | `79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c` |
| left STL | `5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58` |
| right STL | `9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565` |

Thingiverse metadata identifies the model as by **kepeo**, licensed Creative Commons Attribution.

### Type-C source geometry

The STEP is ball-centred: ball center = local `(0, 0, 0)`.

- bounding box X: `-9.631504603 .. +27.963306547`
- bounding box Y: `-14.998377044 .. +15.000000000`
- bounding box Z: `-18.000000100 .. +13.200000100`
- envelope: **37.594811 × 29.998377 × 31.200000 mm**
- housing/switchplate mounting plane: approximately local **Z = -18.0 mm**
- real ball radius: 12.5 mm
- real ball top above mounting plane: **30.5 mm**
- mounting pilots: approximately `(6.200000,+7.980000)` and `(6.224641,-7.980000)`
- measured screw spacing: **15.96 mm**, nominal 16 mm
- screw-pair midpoint: approximately **6.212 mm toward the sensor side from ball center**

Use the actual STEP for production geometry rather than a rounded redraw.

---

## Locked mechanical placement

### Canonical coordinate frame

The placement coordinates below are explicitly **KLOR Gerber/Excellon fabrication coordinates**, in millimetres.

Task 1 solved the KiCad↔fabrication relationship from all 21 MX centers in the NPTH drill data. The fabrication frame is effectively KiCad X unchanged and KiCad Y reflected.

### Locked datums

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Housing screw 1 | **156.111** | **-126.768** |
| Housing screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |
| Deleted SW22 center | **143.025** | **-128.770** |

Interpretation:

- sensor direction: fabrication-frame **-X**
- ball → screw midpoint: about 6.212 mm toward -X
- screw midpoint → breakout center: 13 mm farther toward -X
- screw pair axis: approximately fabrication-frame Y
- Type-C housing screws are a **housing-to-switchplate interface**, not main-PCB mounting holes

The deleted-switch datum resolves to source PCB footprint `SW22` with approximately 0.000045 mm error.

### Verified coordinate transforms

KiCad PCB → Gerber/Excellon:

```text
R = [[ 1.000000000,  0.000000342],
     [ 0.000000342, -1.000000000]]
t = [-0.000089, -0.000052] mm
```

- 21/21 matched centers
- RMS residual: **0.000181 mm**

KiCad PCB → native Konrad switchplate STL:

```text
R = [[ 0.999999991,  0.000131877],
     [ 0.000131877, -0.999999991]]
t = [-80.655587, 153.995244] mm
```

- 18/18 Konrad MX openings matched
- RMS residual: **0.020019 mm**

Native switchplate → native right-case STL:

```text
R = [[ 0.999999999,  0.000033962],
     [-0.000033962,  0.999999999]]
t = [80.582795, 55.951799] mm
```

- 8/8 structural M2 axes matched
- RMS residual: **0.006063 mm**

### Stock mechanical stack-up

The stock case support plane is native case `Z = -0.8 mm`. KLOR specifies 7 mm M2 standoffs; the stock 3DP switchplate is 1.5 mm thick.

Therefore the installed stock stack is:

- switchplate bottom: case `Z = 6.2 mm`
- switchplate top / Type-C mounting plane: case `Z = 7.7 mm`
- stock case top: case `Z = 8.800025 mm`
- case lip above switchplate: about **1.100 mm**
- 25 mm ball top: case `Z = 38.2 mm`
- Type-C housing rim top: about case `Z = 38.9 mm`
- ball is about **0.7 mm below the housing rim**

### Placement in native source-model frames

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

---

## Task 1 clearance results

Using a conservative 18 × 18 mm keycap XY envelope, the closest retained PCB switches clear the Type-C housing:

- `SW15`: **2.654 mm**
- `SW21`: **3.444 mm**
- `SW13`: **4.022 mm**
- `SW12`: **4.424 mm**

Other conservative XY clearances:

- right encoder `SW18`: **27.772 mm**
- MCU `U1` / ProMicro region: **40.321 mm**
- TRRS `J1`: **46.460 mm**

All eight structural M2 axes were also checked against the actual placed housing mesh with a deliberately conservative fastener envelope:

- M2 head: 4.5 mm diameter × 2.0 mm high
- below-plate boss: 6.1 mm diameter
- M2-head collisions: **0/8**
- below-plate boss collisions: **0/8**
- nearest structural axis has about **9.159 mm** radial clearance to a housing vertex in the first 3 mm above the plate

### Kivipallur breakout/service path

The Kivipallur breakout Edge.Cuts are **22 × 25 mm**. Klorball35 uses a **2 × 22 mm** reference pass-through.

Task 1 verified the intended orientation:

- the breakout 22 mm short edge aligns with the 22 mm slot dimension
- the 2 mm slot dimension clears PCB thickness
- the breakout extends inward along the sensor direction
- the conservative retained-keycap corridor gap is approximately **8.000 mm**

The orientation and insertion/service path are mechanically valid.

### Stock case shell interference

The **unmodified stock right-case shell intersects the Type-C housing** at the locked placement.

This is expected local material that Task 5 must relieve. It is **not** a reason to move the trackball because:

- all eight structural case/switchplate mounting axes remain clear
- retained switches remain clear
- encoder remains clear
- MCU remains clear
- TRRS remains clear

**Preserve all eight structural mounting axes. Do not move the locked trackball merely to avoid local stock-shell relief.**

---

## PMW3360 electrical/firmware contract — Task 2 locked

Task 2A–2F are complete. The removed-key circuit, GPIO conflicts, connector orientation, PCB nets, QMK ownership, and complete interface are frozen. Task 3 is authorized to implement the right-hand PCB derivative against this contract.

### Physical keyboard-side connector

The Kivipallur breakout itself is `1=GND ... 7=CS`. The proven opposite-facing keyboard-side mate is deliberately reversed:

| KLOR connector pin | Breakout signal | Target KLOR net | MCU / source |
| ---: | --- | --- | --- |
| 1 | CS | `PMW_CS` | GP9 / U1.12, stock `AUDIO` |
| 2 | MISO | `PMW_MISO` | GP4 / U1.7, stock `RX` |
| 3 | MOSI | `PMW_MOSI` | GP3 / U1.6, stock `SCL` |
| 4 | SCK | `PMW_SCK` | GP2 / U1.5, stock `SDA` |
| 5 | MOTION | NC | no MCU assignment |
| 6 | +3V3 | `VCC` | U1.21 / controller VCC rail |
| 7 | GND | `GND` | controller ground rail |

The keyboard-side connector remains on `F.Cu`, with Task 2C handedness and the opposite-facing `N <-> 8-N` mating rule unchanged.

### Power-net correction

Earlier planning used `3V3` as shorthand for the KLOR-side supply. The actual stock KLOR schematic/PCB names this rail **`VCC`**. With the selected Elite-Pi controller, this is the 3.3 V controller rail.

Therefore:

```text
Kivipallur +3V3 -> KLOR VCC
Kivipallur GND  -> KLOR GND
```

Task 3 must not invent a second KLOR `3V3` rail just to mirror the breakout label.

### Locked stock-circuit dispositions

- GP1 remains half-duplex split serial and `TX -> J1.4` is preserved.
- GP4 becomes `PMW_MISO`; TRRS `J1.3` must be made NC by removing the Task 2B-verified adjacent F.Cu branch.
- GP2 becomes `PMW_SCK`; stock I2C/PAW3204 ownership is disabled and legacy I2C jumpers remain open.
- GP3 becomes `PMW_MOSI`; stock I2C/PAW3204 ownership is disabled, J2 haptic is DNP, and legacy I2C jumpers remain open.
- GP9 becomes `PMW_CS`; audio is disabled and BZ1 must not be an active load.
- MOTION remains electrically unconnected for revision 1.
- Right OLED, haptic, audio, and stock PAW3204 remain disabled/unpopulated for revision 1.

Canonical Task 2 overview:

- [`../design/task2/README.md`](../design/task2/README.md)

Canonical Task 2 evidence also includes:

- `../design/task2/TASK2A_RESULT.md`
- `../design/task2/TASK2B_RESULT.md`
- `../design/task2/TASK2C_RESULT.md`
- `../design/task2/TASK2D_RESULT.md`
- `../design/task2/TASK2E_RESULT.md`
- `../design/task2/TASK2F_RESULT.md`
- `../design/task2/task2_manifest.yaml`

### Locked QMK ownership from Task 2E

The trackball variant uses QMK PMW3360 support over SPI0:

```text
GP2 = SPI0 SCK
GP3 = SPI0 MOSI
GP4 = SPI0 MISO
GP9 = PMW3360 CS
GP1 = half-duplex split serial
GP0 = RGB
```

Required firmware configuration includes `POINTING_DEVICE_DRIVER = pmw3360`, explicit SPI0 pin overrides, `SPLIT_POINTING_ENABLE`, `POINTING_DEVICE_RIGHT`, and preserved `EE_HANDS`.

The trackball build disables OLED, haptic, audio/music, I2C1, stock PAW3204 ownership, and audio PWM4. Both stock default and Vial keymap rules currently re-enable OLED/audio/haptic, so neither may be reused unchanged.

MOTION remains unused. Pointer rotation/inversion, CPI, lift-off distance, scrolling, acceleration, and auto-mouse behavior remain Task 7 bring-up work.

Task 2F passed. Task 3 production PCB implementation is authorized. The canonical final contract is `../design/task2/TASK2F_RESULT.md`.

---

## RGB target

Delete the RGB device associated with SW22/R34 and permanently bypass it in copper:

`previous LED DOUT -> next LED DIN`

Target topology:

- left: 20
- right: 19
- total: 39

Firmware needs an asymmetric 20/19 LED map and a trackball-specific `g_led_config`.

---

## Remaining implementation sequence

### Task 2 — electrical + firmware interface — COMPLETE

Tasks 2A–2F are complete. The final connector/net/GPIO/firmware table is frozen in `../design/task2/TASK2F_RESULT.md`. Reopen Task 2 only if the connector order, GPIO assignments, power-net mapping, stock-circuit dispositions, or firmware ownership must change.

### Task 3 — right-hand trackball PCB derivative — IN PROGRESS

Task 3 is decomposed as `3A → 3B → 3C → 3D → 3E → 3F → 3G`. See [`../design/task3/README.md`](../design/task3/README.md).

Task 3A created the non-destructive schematic-driven KiCad derivative at `../PCB/konrad_trackball/`. Stock `klor1.4/PCB/klor1_4/` remains reference-only. Stock Gerbers were not copied.

Task 3B implemented the frozen Task 2 contract in `konrad_trackball.kicad_sch`:

- SW22 and D22 removed from the derivative schematic;
- `SW13 DOUT → SW14 DIN` direct RGB bypass;
- U1-side ownership changed to `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- new connector `J4`: `1=PMW_CS, 2=PMW_MISO, 3=PMW_MOSI, 4=PMW_SCK, 5=NC, 6=VCC, 7=GND`;
- J1.3 explicitly NC; J1.4/TX preserved;
- J2, OLED1, and BZ1 marked DNP for revision 1.

The derivative PCB intentionally remained the stock baseline through 3B.

Task 3C synchronized that contract onto the PCB:

- SW22 and D22 physically removed;
- deleted-key matrix branches and local D22 net removed while `col1` and `row3` remain distinct;
- `RX` retired and J1.3 made no-net;
- J1.4/TX preserved;
- U1 pads reassigned to `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- permanent B.Cu `SW13 DOUT → SW14 DIN` bypass implemented;
- J4 added with the frozen pin contract.

The Task 3C audit proves stock Edge.Cuts and all unrelated retained footprint/trace/via geometry remain unchanged.

Task 3D then implements the mechanical PCB interface:

- locked pass-through center: Gerber `(143.111,-134.748)`, KiCad `(143.111043,134.747997)`;
- J4 pin-1/anchor: KiCad `(147.724665,142.367997)`, rotation 0°, `F.Cu`;
- J4 row midpoint: `(147.724665,134.747997)`, preserving the proven +4.613622 mm X guide offset;
- fabricated opening: open 2 mm edge notch following the 2×22 mm Klorball service envelope;
- local +X support tongue: right edge X=150.0, bottom edge Y=144.25;
- VCC wraps around the notch and one VCC via moves to `(145.3,133.81)`;
- RGB bypass is shortened on B.Cu to `(151.129969,128.715031) → (151.705,130.22)`.

The 3D audit confirms an empty pass-through corridor, closed Edge.Cuts topology, local copper clearances, and no PMW routing added prematurely.

Task 3E routes the frozen interface without changing Task 3D geometry:

- `PMW_CS` / GP9 → J4.1;
- `PMW_MISO` / GP4 → J4.2;
- `PMW_MOSI` / GP3 → J4.3;
- `PMW_SCK` / GP2 → J4.4;
- J4.5 MOTION remains NC;
- J4.6 ties into `VCC`;
- J4.7 ties into `GND`.

The 3E source audit proves the change is additive only and all six required routed nets are connected. Full KiCad DRC and final preservation classification remain Task 3F.

**Next: Task 3F — preservation, zone refill, integrated DRC, and unrouted review.**

Create a distinct right-hand derivative from stock KLOR. Do not convert the stock reversible PCB into a universal trackball board.

Required direction:

- remove SW22/R34
- bypass its RGB device in copper
- preserve retained switches and encoder
- add Kivipallur electrical interface
- route GP2/GP3/GP4/GP9
- isolate GP4 from optional full-duplex TRRS TX
- provide breakout pass-through/edge clearance
- alter board outline only where necessary
- move/remove D22 or other parts only when audited geometry requires it
- run KiCad DRC

### Task 4 — right Konrad switchplate

Use the STEP source of truth. Add:

- Type-C mounting points from actual housing CAD
- local housing relief
- breakout pass-through/edge relief
- deletion/relief of the R34 opening as required

Preserve unaffected openings and all verified structural mounting axes.

### Task 5 — editable right-case derivative

The stock regular right case is STL-only in this repository:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

Establish a reproducible editable CAD workflow, then provide the **local shell relief proven necessary by Task 1**. Preserve the eight structural mount axes and validate printability/wall thickness/service access.

### Task 6 — final modified-assembly validation

Assemble the actual modified PCB + switchplate + housing + ball + breakout + retained keys + encoder + case and freeze final fabrication geometry.

### Task 7 — QMK trackball variant

Create a trackball-specific Konrad firmware variant:

- 39-key behavior with SW22/R34 absent
- RGB 20 left / 19 right / 39 total
- trackball-specific `g_led_config`
- PMW3360 SPI0: GP2/GP3/GP4, CS=GP9
- right-half-only pointing device
- split GP1 half-duplex
- right encoder retained
- OLED/haptic/audio/PAW3204 disabled initially

Suggested bring-up order:

1. matrix
2. split transport
3. encoder
4. RGB chain/map
5. SPI communication
6. PMW3360 motion
7. pointer orientation/scaling

### Task 8 — fabrication and hardware bring-up

Only after Tasks 1–7 pass:

- regenerate Gerbers/drills
- independently review fabrication outputs
- export final printable CAD
- prepare BOM/assembly notes
- fabricate first revision
- continuity/power test before MCU/sensor installation
- keyboard bring-up first, then PMW3360

---

## Fabrication gate

Task 1 mechanical placement is locked, but **the project as a whole is not fabrication-locked**.

Do not order the modified PCB or treat printed parts as final until Tasks 2–7 pass their completion gates.

If the locked Task 1 XY placement is ever changed, rerun the Task 1 mechanical audit and update together:

- this handoff
- `design/konrad_trackball_geometry.yaml`
- `design/task1/reference_assembly_manifest.yaml`

---

## Source files already reviewed

KLOR:

- `klor1.4/PCB/klor1_4/klor1_4.kicad_sch`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- `klor1.4/PCB/klor1_4/gerbers/klor1_4-NPTH.drl`
- `klor1.4/PCB/klor1_4/KLOR.pretty/`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/`
- `klor1.4/FABNOTES.md`
- `klor1.4/docs/buildguide_3DP.md`
- `klor1.4/case/3DP/konrad/`

Klorball35 / Kivipallur:

- `klorball35/README.md`
- `klorball35/config.yml`
- `klorball35/kicad/klorball35_right/`
- `klorball35/output/pcbs/Klorball35_plate_right.kicad_pcb`
- `klorball35/kicad/Kivipallur_PMW3360_breakout/`

Third-party mechanical reference:

- kepeo, Thingiverse 6719828, `Keyball 25mm Trackball Case Type C`

## Next agent: start here

Continue **Task 3F — preservation and integrated DRC audit** in the derivative project at `PCB/konrad_trackball/`. Treat the Task 3E PCB as the electrical-routing baseline. Refill zones for validation, run KiCad DRC/unrouted checks, classify intentional exceptions, and prove unrelated stock geometry/circuitry remains preserved.

Treat these as locked inputs:

- Task 1 mechanical placement and fabrication datums;
- Task 2 electrical/firmware interface, summarized in [`../design/task2/README.md`](../design/task2/README.md) and frozen in `../design/task2/TASK2F_RESULT.md`.

Do not revisit Task 1 placement or Task 2 connector/net/GPIO/firmware ownership unless implementation uncovers a hard constraint that invalidates one of their verified assumptions.

## PCB representation policy

Committed PCB sources omit generated KiCad `filled_polygon` cache data. Refill zones before DRC or fabrication. Normalized stock PCB: `3dea93bc4266541e9ca85eebc70e4b8c851afc11`; Task 3C PCB: `c3fefdb583d653a836d2ab99a9d94126ea331a3b`; Task 3D PCB: `4272f9c3895fd46c0688b3eb530fc7299b540727`; Task 3E PCB: `cdc63c3081881861bdcba8f0c6bc03a5b242baed`.
