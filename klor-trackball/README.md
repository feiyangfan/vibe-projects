# KLOR Trackball

## Goal

Modify the right half of **KLOR 1.4 MX** using the **Konrad** layout so it gains the same 25 mm PMW3360 trackball system used by Klorball35, while making the smallest practical change to the right-hand PCB.

The design priority is to preserve the existing KLOR architecture wherever possible:

- MX switches and the KLOR 1.4 south-facing SK6812 Mini-E RGB arrangement
- the existing key matrix
- half-duplex split communication
- the rotary encoder
- all unaffected switch positions
- the stock left half

Only components and routes that conflict electrically or mechanically with the trackball should be removed or changed.

## Audited design baseline

### Base keyboard

- PCB: KLOR 1.4 main MX version
- layout: Konrad
- controller: RP2040 Pro Micro-compatible board / Elite-Pi-compatible pinout
- left PCB: stock and unchanged
- right PCB: custom derivative of KLOR 1.4

KLOR Konrad is a 40-key layout. Replacing one right thumb key with the trackball produces:

| Half | Keys |
| --- | ---: |
| Left | 20 |
| Right | 19 |
| Total | 39 |

### Right-hand thumb layout

The Konrad right thumb cluster contains R32, R33, and R34.

For this project:

- retain R32
- retain R33
- replace R34 / matrix position `[7,1]` / SW22 with the trackball
- retain the right rotary encoder
- do not reposition R32 or R33

This follows the same high-level idea as Klorball35: the right hand gives up one thumb key to make room for the trackball.

### What is actually removed

The minimum intended component removal is:

- SW22 / R34
- the RGB LED integrated into the SW22 footprint

D22 is associated with SW22, but it does **not** have to be deleted purely for electrical reasons. Remove D22 only if it conflicts with the final trackball housing, sensor breakout, or board outline. Otherwise it may remain as an unpopulated footprint.

## Trackball system

Use the same trackball stack as Klorball35 rather than redesigning the sensor electronics onto the KLOR PCB.

### Mechanical / sensor components

- ball: 25 mm
- sensor: PixArt PMW3360DM-T2QU
- sensor PCB: Kivipallur PMW3360 breakout
- housing: kepeo 25 mm Trackball Case Type C, Thingiverse 6719828

The Kivipallur breakout already contains the PMW3360 support circuitry, including the 3.3 V / 1.8 V power circuitry, so the KLOR right PCB only needs to provide power and SPI signals to the breakout.

## PMW3360 electrical interface

The Kivipallur breakout exposes a 7-pin interface.

| Breakout pin | Signal | KLOR right connection |
| ---: | --- | --- |
| 1 | GND | GND |
| 2 | 3.3 V | 3V3 |
| 3 | MOTION | NC |
| 4 | SCK | GP2 |
| 5 | MOSI | GP3 |
| 6 | MISO | GP4 |
| 7 | CS | GP9 |

MOTION is intentionally left unconnected for the initial design. Normal PMW3360 operation can use polling, so the trackball only consumes four MCU GPIOs.

## GPIO plan

### PMW3360

| Signal | RP2040 GPIO | Existing KLOR use / required action |
| --- | --- | --- |
| SCK | GP2 | repurpose from right-side I2C / stock PAW3204 use |
| MOSI | GP3 | repurpose from right-side I2C / stock PAW3204 use |
| MISO | GP4 | isolate from optional full-duplex TX / TRRS route, then use as SPI MISO |
| CS | GP9 | repurpose from audio |

GP2 / GP3 / GP4 form a valid RP2040 SPI0 hardware bus:

- GP2 = SPI0 SCK
- GP3 = SPI0 TX / MOSI
- GP4 = SPI0 RX / MISO

GP9 is used as a normal GPIO chip-select.

### Retained assignments

These remain unchanged:

- RGB: GP0
- split serial: GP1, half-duplex
- matrix rows: GP5 / GP6 / GP7 / GP8
- matrix columns: GP20 / GP21 / GP22 / GP23 / GP26 / GP27
- encoder: GP28 / GP29

The Klorball35 native PMW3360 pin assignment must **not** be copied directly because its SPI pins overlap KLOR 1.4 matrix-column GPIOs. Reusing those pins would require a much larger matrix reroute and would violate the minimal-edit goal.

## Right-side optional features

The revised design should distinguish between **removing a feature** and **removing its footprint**.

### OLED

- keep the physical OLED footprint unless it interferes mechanically
- do not populate the right OLED
- leave its existing I2C connection/jumpers open

GP2 / GP3 become SPI pins on the right MCU, so the right side cannot use the stock I2C OLED at the same time.

### Haptic driver

- keep the haptic footprint unless it interferes mechanically
- do not populate the right haptic module
- leave its connection/jumpers open

The left half may still retain I2C peripherals later if firmware initialization is made side-aware.

### Audio

- keep the speaker footprint unless it interferes mechanically
- do not populate the right speaker
- GP9 becomes PMW3360 CS

### Stock PAW3204 trackball support

- do not use the PAW3204 module
- old PAW3204 pads/routes may remain if they do not create an electrical or mechanical conflict
- GP2 / GP3 are reassigned to PMW3360 SPI

This approach minimizes PCB edits and avoids deleting footprints merely because they are unused.

## Split communication and GP4

KLOR 1.4 normally uses GP1 for half-duplex serial communication between halves.

The PCB also supports an optional RP2040 full-duplex arrangement where GP4 is routed as TX and GP1 as RX through the TRRS connection.

For this project:

- keep GP1 half-duplex split communication unchanged
- do not enable the optional full-duplex mode
- physically disconnect GP4 from the right-hand TX / TRRS route
- route GP4 only to PMW3360 MISO on the right half

This is a required PCB edit. Firmware configuration alone is not sufficient because the existing copper route would otherwise still connect GP4 to the TRRS path.

## RGB topology

KLOR already includes a `lost thumb?` bypass for moving from the four-thumb Polydactyl layout to the three-thumb Konrad layout.

This project removes one additional right-thumb RGB device with SW22.

The custom right PCB should therefore permanently route the RGB data chain around the deleted SW22 LED:

```text
previous LED DOUT -> next LED DIN
```

A user-facing solder jumper is not required unless there is a specific reason to support both the stock and trackball variants on the same PCB.

Final target RGB count:

| Half | LEDs |
| --- | ---: |
| Left | 20 |
| Right | 19 |
| Total | 39 |

Firmware will need a dedicated asymmetric 20/19 RGB configuration and LED map. Simply changing the total LED count is not enough.

## Mechanical architecture

The trackball assembly spans multiple parts. Do not treat all Klorball35 mounting geometry as belonging to the main keyboard PCB.

### Right main PCB

Expected changes:

- remove SW22 / R34 area
- add PMW3360 breakout slot / clearance
- add the 7-pin breakout electrical connection
- reroute GP2 / GP3 / GP4 / GP9 locally
- isolate GP4 from the full-duplex TX / TRRS path
- bypass the deleted SW22 RGB LED
- modify the board outline only where necessary for trackball clearance

### Right switch plate

The Klorball35 / Kivipallur geometry places the Type-C housing mounting holes in the right switchplate design rather than simply duplicating them into the main PCB.

Verified reference geometry so far:

- Type-C housing mounting-hole pair: 16 mm center-to-center
- PMW3360 breakout reference slot: 2 mm x 22 mm
- breakout centerline: 13 mm laterally from the mounting-hole midpoint

The final hole diameter, housing envelope, and exact ball-center datum must still be verified against the actual Type-C housing CAD/STL before fabrication.

### Right case

The right case must be modified only after the final housing position and ball center are known. Required checks include:

- housing outer envelope
- 25 mm ball clearance
- ball height above the switchplate
- clearance to R32 / R33
- clearance to encoder, MCU, TRRS, and existing case walls
- sensor-breakout vertical position and access

## Firmware direction

The final QMK configuration should support a pointing device only on the right half and explicitly configure the PMW3360 SPI pins.

Target direction:

- PMW3360 pointing-device driver enabled
- pointing device located on the right half
- SPI0 explicitly configured for GP2 / GP3 / GP4
- PMW3360 CS on GP9
- half-duplex split communication retained on GP1
- RGB updated to 20 left / 19 right
- right-side I2C initialization disabled or made side-aware
- right-side audio disabled

For first hardware bring-up, the safest firmware path is to disable OLED, haptic, and audio globally, validate matrix + split + encoder + RGB + PMW3360, and then restore left-only optional peripherals if desired.

## Minimal-change summary

The intended electrical PCB modifications are limited to:

1. remove SW22 / R34 and its integrated RGB position
2. remove D22 only if needed for mechanical clearance
3. physically isolate GP4 from the optional full-duplex TX / TRRS route
4. route GP2 / GP3 / GP4 / GP9 to the Kivipallur PMW3360 breakout connector
5. permanently bypass the removed SW22 LED in the RGB chain
6. add only the board cutout / outline changes required by the trackball assembly

The following should remain unchanged:

- the left PCB
- MCU footprint
- GP0 RGB architecture
- GP1 half-duplex split architecture
- matrix rows and columns
- encoder wiring
- R32 and R33
- all other MX switch positions
- all unaffected south-facing RGB footprints

## Current design status

### Considered locked unless new source evidence contradicts it

- KLOR 1.4 MX as the base
- Konrad layout as the base key arrangement
- 39-key final layout: 20 left + 19 right
- R34 / SW22 replaced by trackball
- R32 / R33 retained
- encoder retained
- Klorball35 25 mm Type-C / PMW3360 / Kivipallur trackball stack
- breakout pins 1-7: GND, 3V3, MOTION, SCK, MOSI, MISO, CS
- MOTION left NC initially
- PMW GPIOs: GP2 / GP3 / GP4 / GP9
- GP1 half-duplex split retained
- GP4 physically isolated from optional full-duplex TRRS TX
- final RGB target: 20 left / 19 right / 39 total

### Still unresolved

- exact Type-C housing CAD/STL dimensions
- exact ball-center datum
- exact trackball XY position on the KLOR right half
- whether D22 physically conflicts and therefore must be deleted
- exact right-board edge modification
- exact right switchplate opening and mounting-hole geometry after CAD overlay
- final right case geometry
- final QMK implementation details and side-aware peripheral initialization

Do **not** generate fabrication files until the Type-C housing CAD/STL has been verified and the complete mechanical overlay has been checked.

## Reviewed project sources

The audited design was derived or cross-checked from these repository files:

- `klor1.4/PCB/klor1_4/klor1_4.kicad_sch`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- `klor1.4/PCB/klor1_4/KLORlib.kicad_sym`
- `klor1.4/PCB/klor1_4/KLOR.pretty/`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/klor.c`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/rules.mk`
- `klor1.4/FABNOTES.md`
- `klor1.4/docs/buildguide_3DP.md`
- `klorball35/README.md`
- `klorball35/config.yml`
- `klorball35/kicad/klorball35_right/klorball35_right.kicad_sch`
- `klorball35/kicad/klorball35_right/klorball35_right.kicad_pcb`
- `klorball35/output/pcbs/Klorball35_plate_right.kicad_pcb`
- `klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_sch`
- `klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb`

Upstream RP2040 and QMK documentation was also used to cross-check SPI capability and the intended split-pointing-device architecture.

## Next engineering step

Before modifying the KiCad PCB, obtain and inspect the Type-C housing CAD/STL and establish the exact ball center, housing envelope, and sensor relationship. Then overlay that geometry onto the KLOR 1.4 right PCB around R34 and verify clearance to R32, R33, the encoder, MCU, TRRS, board edge, and case.
