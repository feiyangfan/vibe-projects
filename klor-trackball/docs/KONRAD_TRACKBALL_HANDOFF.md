# KLOR 1.4 MX + 25 mm Trackball — Konrad Engineering Handoff

## Purpose

This document is the canonical handoff for the KLOR trackball modification. A future agent should be able to continue PCB, switchplate, case, and firmware work from this file without reconstructing the design history from chat.

The target is a **KLOR 1.4 MX, Konrad layout** with a **25 mm PMW3360 trackball on the right half**, derived from the mechanical/electrical approach used by Klorball35 while preserving as much of KLOR 1.4 as practical.

The left half remains stock.

## Design decisions that are already locked

### Keyboard/layout

- Base PCB: `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- Base layout: **Konrad**
- Switch type: **MX**, retaining KLOR 1.4 south-facing SK6812 Mini-E RGB architecture
- Final key count target: **39 keys**
  - left: 20
  - right: 19
- Right rotary encoder: **retain**
- Right thumb keys:
  - R32: retain
  - R33: retain
  - R34 / SW22 / matrix `[7,1]`: remove and replace with trackball
- Do not move R32 or R33 merely to make room for the trackball.

### Trackball stack

Use the proven Klorball35-style external sensor assembly rather than integrating PMW3360 support circuitry directly onto the KLOR PCB.

- Ball: 25 mm
- Sensor: PixArt PMW3360DM-T2QU
- Sensor breakout: Kivipallur PMW3360 breakout
- Housing: kepeo **Keyball 25mm Trackball Case Type C**, Thingiverse 6719828

### PMW3360 electrical interface

Kivipallur breakout pinout:

| Pin | Signal | KLOR right connection |
| ---: | --- | --- |
| 1 | GND | GND |
| 2 | 3.3 V | 3V3 |
| 3 | MOTION | NC for initial revision |
| 4 | SCK | GP2 |
| 5 | MOSI | GP3 |
| 6 | MISO | GP4 |
| 7 | CS | GP9 |

GPIO plan:

- GP2 = SPI0 SCK
- GP3 = SPI0 TX / MOSI
- GP4 = SPI0 RX / MISO
- GP9 = PMW3360 CS
- GP1 remains KLOR half-duplex split serial
- GP0 remains RGB
- GP5/6/7/8 remain matrix rows
- GP20/21/22/23/26/27 remain matrix columns
- GP28/29 remain encoder

Required PCB electrical edit: **physically isolate GP4 from the optional full-duplex TX/TRRS route**. Firmware configuration alone is not sufficient because the copper connection would remain.

### Optional right-side peripherals

The goal is minimal PCB disturbance. Unused footprints may remain unless they mechanically collide.

- Right OLED: do not populate; stock right-side I2C cannot be used because GP2/GP3 become SPI.
- Right haptic module: do not populate.
- Right speaker/audio: do not populate; GP9 becomes trackball CS.
- Stock PAW3204 support: do not use; pads/routes can remain if electrically harmless and mechanically clear.

### RGB

SW22/R34's integrated RGB position is deleted. Permanently bypass that device in the right-half RGB chain:

`previous LED DOUT -> next LED DIN`

Target RGB topology:

- left: 20
- right: 19
- total: 39

Firmware must use an asymmetric 20/19 map; changing only the total LED count is insufficient.

---

## Type-C housing CAD audit

The missing mechanical source was obtained and inspected directly from the Thingiverse 6719828 download.

Archive name used during the audit:

`Keyball 25mm Trackball Case Type C - 6719828.zip`

Contained CAD/model files:

- `files/keyball_trackball_case_25mm_type_c.stp`
- `files/keyball_trackball_case_25mm_type_c_left.stl`
- `files/keyball_trackball_case_25mm_type_c_right.stl`

The STEP is the preferred source for dimensions.

### Exact source hashes

These hashes identify the exact third-party files used for the mechanical measurements:

| File | SHA-256 |
| --- | --- |
| ZIP archive | `ad2ee79388c01fcb775ee08e35761d14b27fbd53ecffabfbdc45add77830e206` |
| `README.txt` | `51830328ac04a21fd0c48dae2aded484cc5560fc1dad66f6cd4218e766eef783` |
| `LICENSE.txt` | `77aaab67a7fc3d544c38e2c075b7134dc8000fcf5391c7b0120735ab8162d503` |
| Type-C STEP | `79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c` |
| left STL | `5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58` |
| right STL | `9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565` |

Thingiverse metadata included in the archive says the model is by **kepeo** and licensed **Creative Commons Attribution**.

### Type-C coordinate system and measured geometry

The STEP contains the ball-centred geometry. Measurements below are in millimetres.

- Ball center: **model origin `(0, 0, 0)`**
  - verified from spherical CAD surfaces centred at the origin
- Overall STEP bounding box:
  - X: `-9.631504603 .. +27.963306547`
  - Y: `-14.998377044 .. +15.000000000`
  - Z: `-18.000000100 .. +13.200000100`
- Envelope size: **37.594811 × 29.998377 × 31.200000 mm**
- Housing/switchplate mounting plane: approximately **Z = -18.0 mm**
- Actual 25 mm ball radius: 12.5 mm
- Actual ball top above mounting plane: **30.5 mm**

The STEP includes spherical housing surfaces at radii 15.0 mm and 13.25 mm centred at the ball origin. These are housing/cavity geometry, not the physical trackball diameter.

### Housing mounting holes

The two mounting pilots are nominally a **16 mm pair** and are aligned along the local Y axis.

Measured pilot axes from the STEP:

- `(X=6.200000, Y=+7.980000)`
- `(X=6.224641, Y=-7.980000)`

Pilot cylinder radius is 0.8 mm. The slight X asymmetry is part of the source CAD; use the actual CAD for production geometry rather than rounding every feature to a simplified sketch.

Useful nominal values:

- screw spacing: **15.96 mm measured / 16 mm nominal**
- screw-pair midpoint: approximately **6.212 mm from ball center toward the sensor side**

---

## Klorball35 reference geometry

`klorball35/config.yml` establishes the interface relationship used by the known working Klorball35 design:

- two housing/switchplate screw positions: **16 mm center-to-center**
- PMW3360 breakout reference slot: **2 mm × 22 mm**
- breakout-slot centerline: **13 mm from the screw-pair midpoint toward the sensor side**

The mounting screws are a **housing-to-switchplate interface**. Do not automatically duplicate those screw holes into the KLOR main PCB.

The main PCB needs clearance/pass-through for the vertical Kivipallur breakout plus the electrical interface.

---

## Candidate placement on KLOR 1.4 Konrad

All PCB coordinates below use the native KLOR KiCad/Gerber coordinate system in millimetres.

The current placement intentionally puts the ball outside/right of the deleted R34 region while sending the sensor/breakout inward toward the former switch corridor.

### Placement datums

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Screw 1 | **156.111** | **-126.768** |
| Screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |

Interpretation:

- sensor direction is global **-X** from the ball center
- ball -> screw midpoint: approximately 6.212 mm toward -X
- screw midpoint -> breakout center: 13 mm farther toward -X
- screw pair runs approximately along global Y

This matches the Type-C/Klorball35 relationship while locating the ball where the Konrad thumb cluster can accept it with one key removed.

### Deleted-switch reference

From the KLOR rev1.4 manufacturing drill data, the R34/SW22 MX center is approximately:

`(143.025, -128.770)`

The breakout center is therefore only about 0.086 mm away in X from the deleted switch centerline, with a Y offset of about -5.978 mm. This is why the deleted R34 corridor is the correct place for the sensor pass-through.

### Housing 2D envelope at this placement

Using the current orientation (`global X = ball_X - model_X`, `global Y = ball_Y + model_Y`), the Type-C STEP AABB projects to approximately:

- X: **134.360 .. 171.955 mm**
- Y: **-149.746 .. -119.748 mm**

This envelope strongly overlaps R34/SW22, confirming that switch cannot remain.

Using an 18 mm square keycap envelope for the adjacent retained R33 position at approximately X=121.915 mm, the simple X-edge clearance to the Type-C AABB is approximately **3.445 mm**. This is a conservative rectangular-envelope sanity check, not a final 3D collision result.

### Switchplate/case implication

The stock Konrad switchplate cannot remain geometrically untouched. Preliminary overlay work indicates a local outward relief on the order of **6–7 mm maximum** near the trackball area, plus the breakout edge/pass-through.

Do not enlarge the entire keyboard. Modify only the local right thumb/trackball region.

---

## Mechanical architecture to implement

### Right main PCB

Required/expected changes:

1. remove SW22/R34 switch footprint and its integrated RGB device
2. bypass the removed RGB device in copper
3. add the Kivipallur 7-pin electrical connection
4. route GP2/GP3/GP4/GP9 locally to the breakout
5. physically isolate GP4 from optional full-duplex TRRS TX
6. provide the breakout pass-through / edge clearance corresponding to the 2 × 22 mm reference slot
7. alter the board outline only where the Type-C assembly requires it
8. remove or relocate D22 only if the actual layout/collision audit requires it
9. relocate any other small components/tracks only if they intersect the housing/breakout corridor

Do **not** add the two Type-C housing mounting screws to the main PCB unless a later mechanical redesign intentionally changes the architecture.

### Right switchplate

Modify the Konrad right switchplate to:

- accept the Type-C housing using its two approximately 16 mm-spaced mounting locations
- create the necessary local outer profile/relief for the Type-C housing
- provide the vertical Kivipallur breakout pass-through/edge relief
- preserve all unaffected MX openings and mounting features

Use the source STEP for final hole/profile placement rather than only the rounded nominal dimensions in this document.

Relevant KLOR files:

- `klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.step`
- `klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.stl`
- `klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.dxf`
- `klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.svg`

### Right Konrad case

Proceed with **Konrad**. The stock right case source exists in the repository:

- `klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

The right case needs a local trackball modification around the candidate placement. Preserve the stock left case and as much of the right case shell as practical.

Final case work must check:

- Type-C housing shell collision
- 25 mm ball access/exposure
- switchplate contact plane
- PMW3360 breakout and cable/header access
- R32/R33 keycap and switch-body clearance
- encoder clearance
- MCU/TRRS clearance
- case wall thickness and printability

---

## What is confirmed vs. what still needs engineering work

### Confirmed / design intent locked

- KLOR 1.4 MX + Konrad
- left half stock
- R34/SW22 deleted
- R32/R33 retained
- right encoder retained
- 25 mm Type-C / Kivipallur PMW3360 stack
- Type-C CAD dimensions and ball-centred datum
- switchplate-mounted Type-C housing architecture
- PMW3360 breakout reference slot relationship from Klorball35
- PMW GPIOs GP2/GP3/GP4/GP9
- GP1 half-duplex split retained
- GP4 physical isolation from optional full-duplex TRRS TX
- right OLED/haptic/audio not populated for first revision
- right RGB count 19, left RGB count 20
- candidate ball/screw/breakout placement listed above

### Not yet fabrication-locked

The mechanical uncertainty about the Type-C housing itself is closed, but the **modified KLOR parts have not yet been produced or collision-checked as final CAD**.

Before ordering PCBs or printing the final case, complete:

1. exact KiCad component audit around R34, including D22 and nearby passives/tracks
2. exact PCB outline edit and breakout slot/connector geometry
3. final right switchplate CAD edit using the Type-C STEP
4. final right Konrad case CAD edit
5. assembled 3D interference check with PCB + switchplate + Type-C housing + R32/R33 + encoder + case
6. KiCad DRC and fabrication-output review
7. QMK implementation and right-only pointing-device bring-up

The current XY placement is the working baseline. Change it only if a concrete collision or assembly constraint demands it; if changed, update both this document and `design/konrad_trackball_geometry.yaml`.

---

## Firmware bring-up order

For the first hardware revision:

1. keep half-duplex split on GP1
2. validate matrix and encoder
3. validate asymmetric RGB chain after SW22 bypass
4. bring up PMW3360 on SPI0 using GP2/GP3/GP4 and CS=GP9
5. configure pointing device as right-half only
6. keep OLED/haptic/audio disabled initially
7. restore any desired left-only optional peripherals only after basic hardware is stable

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
- exact hashes are recorded above

## Next agent: start here

The next implementation task is **not more research**. It is to edit the right KLOR 1.4 PCB and Konrad mechanical parts using the placement in this handoff.

Recommended order:

1. duplicate/rename the right-board design if needed so stock KLOR sources remain clearly identifiable
2. remove R34/SW22 and inspect D22/passives/traces in KiCad
3. add the breakout clearance and 7-pin interface
4. reroute GP2/GP3/GP4/GP9 and RGB bypass; isolate GP4/TRRS TX
5. run KiCad DRC
6. edit Konrad switchplate around the same datums
7. edit the right Konrad case
8. perform final 3D assembly/collision validation
9. only then generate fabrication files
