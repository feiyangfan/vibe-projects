# KLOR Trackball

## Goal

Modify the right half of KLOR 1.4 MX to use a Klorball35-style 25 mm PMW3360 trackball while preserving MX switches, per-key RGB, the keyboard matrix, split connection, and rotary encoder with the smallest practical PCB changes.

## Current design baseline

### Base

- KLOR 1.4 MX
- Konrad-derived thumb layout
- Klorball35 / Kivipallur mechanical reference
- 25 mm Type-C trackball housing
- PMW3360 breakout

### Right-hand layout

- Retain R32 / R33.
- Replace R34 / SW22 with the trackball.
- Remove SW22, D22, and the RGB LED integrated into the SW22 footprint.
- Retain the rotary encoder.

### PMW3360 pin assignment

| Signal | RP2040 GPIO | Existing KLOR use / action |
| --- | --- | --- |
| SCK | GP2 | Repurpose from I2C / PAW3204 |
| MOSI | GP3 | Repurpose from I2C / PAW3204 |
| MISO | GP4 | Isolate from optional TX / TRRS route first |
| CS | GP9 | Repurpose from audio |
| VCC | 3.3 V | Keep |
| GND | GND | Keep |
| MOTION | NC initially | Leave unconnected initially |

Retained GPIO assignments:

- RGB: GP0
- Split serial: GP1
- Matrix rows: GP5-GP8
- Matrix columns: GP20 / GP21 / GP22 / GP23 / GP26 / GP27
- Encoder: GP28 / GP29

Right-side functions to DNP or disable where no longer required:

- OLED
- Haptic driver
- Audio
- PAW3204 support

The footprints do not need to be removed merely because they are DNP unless they interfere with the trackball mechanically or electrically.

### Mechanical reference

Verified from the Klorball35 / Kivipallur source geometry:

- Trackball mounting-hole pair: 16 mm center-to-center.
- PMW3360 breakout slot: 2 mm x 22 mm.
- PMW3360 breakout centerline: 13 mm from the mounting-hole midpoint.

The exact 25 mm ball-center position relative to these mounting datums is **not yet verified**. Do not manufacture from an estimated ball-center offset. The Type-C housing CAD/STL should be obtained and checked first.

### RGB

KLOR already provides a `lost thumb?` bypass for changing from the stock four-thumb Polydactyl layout to the three-thumb Konrad layout.

This project removes one additional right-thumb RGB position with SW22. The custom right PCB therefore needs the RGB data chain routed around the removed SW22 LED, either permanently or with an explicit solder jumper.

### Split / GP4 constraint

KLOR normally uses GP1 for half-duplex split communication. GP4 is also routed for the optional full-duplex TX path.

Before GP4 is used as PMW3360 MISO on the right half, its existing TX / TRRS connection must be electrically isolated in the PCB design. Firmware configuration alone is not sufficient justification for leaving the copper connection in place.

### Firmware constraint

Both halves may use the same QMK build, so peripheral initialization needs to be reviewed for side awareness:

- The right half will use GP2 / GP3 / GP4 / GP9 for the PMW3360.
- I2C devices on GP2 / GP3 cannot be initialized on the right at the same time.
- Left-side behavior should remain available if those peripherals are retained there.
- The optional full-duplex GP4 path must not be active on the trackball half.

## Reviewed project sources

The current design baseline was derived or cross-checked from these files in this repository:

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
- `klorball35/output/pcbs/Klorball35_plate_right.kicad_pcb`
- `klorball35/kicad/klorball35_right/`
- `klorball35/kicad/Kivipallur_PMW3360_breakout/`

Upstream KLOR/QMK and Kivipallur sources were also used as cross-checks where appropriate; they do not need to be duplicated in this repository.

## Outstanding work

- Obtain/verify the Type-C housing CAD/STL and establish the exact 25 mm ball-center datum.
- Transplant the Klorball35 trackball mounting geometry into the KLOR 1.4 right MX PCB.
- Remove SW22/D22 and repair the RGB data chain.
- Isolate GP4 from the optional TX/TRRS route and route the PMW3360 signals.
- Implement and validate side-aware QMK PMW3360 support.
- Update the right plate and case for the trackball assembly.
- Generate and review fabrication files before ordering.

## Repository cleanup policy

This project keeps editable MX PCB, firmware, case, knob, trackball-reference, and fabrication-reference sources while removing files that are generated/local state or unrelated to the chosen MX design.

The initial cleanup removes:

- `klor1.4/PCB/klor1_4/fp-info-cache`
- `klor1.4/PCB/klor1_4/KLORlib.bak`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_prl`
- `klor1.4/PCB/klor1_4_LP_KS33/`
- `klor1.4/FIRMWARE/Ready-to-flash/`

Stock MX source files and the Klorball35/Kivipallur references remain intact.
