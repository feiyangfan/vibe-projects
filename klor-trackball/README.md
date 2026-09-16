# KLOR Trackball

## Goal

Modify the right half of **KLOR 1.4 MX** using the **Konrad** layout so it gains a 25 mm PMW3360 trackball based on the Klorball35 / Kivipallur architecture, while preserving the stock KLOR design everywhere that does not conflict with the trackball.

The left half remains stock.

## Current status

The previously missing Type-C housing CAD has now been obtained and audited. The basic mechanical architecture and a working KLOR placement are defined.

**The next step is implementation, not more housing research.**

Canonical handoff:

- [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md) — complete electrical/mechanical design state, measurements, decisions, remaining engineering work, and next-agent instructions
- [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml) — machine-readable geometry, GPIO assignments, placement datums, hashes, and fabrication gates

Do not generate fabrication files until the remaining PCB/CAD edits and final interference checks described in the handoff are complete.

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

The Type-C STEP has been measured directly. Important values:

- ball center = CAD origin
- housing envelope ≈ **37.595 × 29.998 × 31.200 mm**
- housing/switchplate mounting plane = approximately **18 mm below ball center**
- top of a real 25 mm ball = **30.5 mm above the mounting plane**
- mounting screw pair = **15.96 mm measured / 16 mm nominal**
- screw-pair midpoint ≈ **6.212 mm toward the sensor side from ball center**

Exact source-file hashes and detailed coordinates are in the handoff and YAML.

## Working mechanical placement

KLOR native PCB/Gerber coordinates, millimetres:

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | **162.323** | **-134.748** |
| Housing screw midpoint | **156.111** | **-134.748** |
| Screw 1 | **156.111** | **-126.768** |
| Screw 2 | **156.111** | **-142.728** |
| PMW3360 breakout-slot center | **143.111** | **-134.748** |

The current orientation puts the ball outside/right of the deleted R34 region and sends the sensor/breakout inward through the former R34 corridor.

The Type-C housing screws belong to the **switchplate/housing interface**, not automatically to the main PCB. The main PCB should instead receive the required Kivipallur breakout clearance/pass-through plus the electrical interface.

## PMW3360 electrical plan

| Breakout signal | KLOR right connection |
| --- | --- |
| GND | GND |
| 3.3 V | 3V3 |
| MOTION | NC initially |
| SCK | GP2 |
| MOSI | GP3 |
| MISO | GP4 |
| CS | GP9 |

Other retained assignments:

- RGB: GP0
- split serial: GP1, half-duplex
- matrix rows: GP5 / GP6 / GP7 / GP8
- matrix columns: GP20 / GP21 / GP22 / GP23 / GP26 / GP27
- encoder: GP28 / GP29

**Required PCB edit:** physically isolate GP4 from KLOR's optional full-duplex TX/TRRS path before using GP4 as PMW3360 MISO.

The right OLED, haptic module, speaker/audio, and stock PAW3204 should remain unpopulated for the first revision. Their footprints may remain if they do not create a mechanical/electrical conflict.

## RGB

Delete the RGB device associated with SW22/R34 and permanently bypass it in copper:

```text
previous LED DOUT -> next LED DIN
```

Target counts:

- left: 20
- right: 19
- total: 39

Firmware needs an asymmetric 20/19 LED map.

## Mechanical work to implement

### Right main PCB

- remove SW22/R34 and its RGB position
- inspect D22 and nearby passives/tracks; relocate/delete only if they conflict
- add Kivipallur 7-pin connection
- add breakout clearance corresponding to the Klorball35 2 × 22 mm reference slot
- route GP2/GP3/GP4/GP9 locally
- isolate GP4 from optional full-duplex TRRS TX
- bypass the deleted RGB device
- alter the board outline only where required

### Right Konrad switchplate

- add the two Type-C housing mounting locations
- add local housing relief
- add the Kivipallur breakout edge/pass-through relief
- preserve all unaffected MX openings and mounting features

Relevant source files are under:

`klor1.4/case/3DP/konrad/switchplate/`

### Right Konrad case

Proceed with **Konrad** and modify only the right case locally around the trackball assembly.

Stock right case source:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

## Fabrication gate

The Type-C housing uncertainty is resolved, but the modified KLOR parts are **not yet fabrication-locked**.

Before ordering/printing:

1. complete exact KiCad component and copper audit around R34, including D22
2. make the PCB outline/breakout changes
3. edit the Konrad switchplate using the Type-C STEP geometry
4. edit the right Konrad case
5. perform a complete assembled 3D interference check
6. run KiCad DRC and fabrication-output review
7. implement and bring up QMK pointing-device support

See [`docs/KONRAD_TRACKBALL_HANDOFF.md`](docs/KONRAD_TRACKBALL_HANDOFF.md) before making changes. If the working XY placement changes, update both the handoff and [`design/konrad_trackball_geometry.yaml`](design/konrad_trackball_geometry.yaml) in the same commit.
