# KLOR Trackball Rev 1 Requirements

## Status

**REV 1 PRODUCT + TASK 2 GEOMETRY FROZEN**

This document is the authoritative product-requirements freeze for Tasks 2–4.

The project is not attempting to preserve every capability of stock KLOR. Rev 1 is a focused, wired, fixed-layout KLOR/Konrad trackball keyboard. Features that do not support that product are intentionally removed rather than carried forward as dormant complexity.

Any change to a **Required** or **Removed** decision below should be treated as a requirements change, not an incidental implementation edit.

---

## Product definition

Build a fabrication-ready split keyboard based on **KLOR 1.4 MX / Konrad** with a **25 mm PMW3360 trackball integrated into the right thumb area**.

Rev 1 must deliver:

- left PCB;
- right PCB;
- left and right switchplates;
- stock-compatible left case or equivalent;
- modified right wired Konrad case;
- PMW3360/Kivipallur trackball assembly;
- QMK firmware;
- fabrication outputs and assembly documentation.

The design must be reproducible from upstream source and must not depend on repeated manual KiCad/CAD coordinate edits.

---

## Frozen decisions

### Layout and ergonomics

| Requirement | Decision |
| --- | --- |
| Base | KLOR 1.4 MX |
| Layout | Fixed **Konrad** only |
| Switch family | Full-height MX |
| Left key count | **20** |
| Right key count | **19** |
| Right thumb keys | **Retain R32 / SW20 and R33 / SW21; remove R34 / SW22 / D22** |
| Total key count | **39 total: 20 left / 19 right** |
| Key geometry | Preserve stock Konrad key centers and rotations except where explicitly modified for the trackball interface |
| Alternative KLOR layouts | Not supported in Rev 1 |
| Break-off / multi-layout PCB geometry | Not supported in Rev 1 |

Task 2 compared the historical R34-only layout with more aggressive thumb/encoder-removal variants and froze the minimum-change Rev-1 architecture: **R32 and R33 retained, R34 removed, right encoder retained**.

Changing that retained-control set after Task 2D is a geometry/requirements change and requires reopening Task 2 rather than being treated as a Task-3 PCB implementation choice.

### PCB architecture

Rev 1 uses **separate left and right PCB outputs**.

There is no requirement for:

- one reversible PCB to serve both hands;
- front/back component reversibility;
- one universal PCB that supports all KLOR layouts.

This is intentional. The right half is mechanically and electrically asymmetric because of the trackball.

The left half should remain geometrically compatible with the stock Konrad layout and case interfaces wherever those interfaces are retained.

### Switches, matrix, and diodes

Required:

- MX-compatible full-height hotswap implementation;
- stock Konrad switch spacing/rotation;
- one matrix diode per retained key;
- **1N4148W / SOD-123-class** diode footprint as the production reference;
- **COL2ROW** matrix direction;
- preserve the stock 4-row / 6-column-per-half topology unless Task 3 demonstrates a compelling implementation reason to change the electrical encoding without changing the physical layout.

### Encoders

The **left encoder is retained**.

The **right EC11-class encoder is retained in its stock location** for Rev 1.

Task 2 found that removing it provides no meaningful placement benefit while R33 is retained; the trackball housing has substantial clearance to the stock encoder. Relocating or removing the right encoder after Task 2D requires reopening the frozen geometry contract.

### RGB

Required:

- per-key RGB;
- **SK6812 Mini-E** production reference;
- south-facing LED orientation;
- one RGB device per retained key;
- **20 LEDs on the left**;
- **19 LEDs on the right**;

There must be no RGB device at any right-thumb position removed by the final Task-2 geometry.

### Controller

Required:

- one **RP2040 Pro Micro-compatible controller per half**;
- Pro Micro-class mechanical footprint/envelope;
- wired USB operation;
- QMK as the Rev-1 firmware platform.

The historical implementation used the Elite-Pi pin model and Klorball35 uses the 0xCB Helios. Rev 1 should remain compatible with the Pro Micro RP2040 ecosystem rather than relying on a unique controller-specific mechanical form factor.

The exact production controller and final GPIO allocation are Task-3 implementation decisions, provided they satisfy this requirements document.

### Split connection

Required:

- TRRS interconnect;
- half-duplex serial split transport;
- one serial data conductor plus power and ground;
- QMK handedness support so the halves are explicitly identified.

Full-duplex split transport is not a Rev-1 requirement.

### Trackball

Required:

- right half only;
- **25 mm ball**;
- **PixArt PMW3360DM-T2QU** sensor;
- **Kivipallur PMW3360 breakout** architecture;
- **Keyball 25 mm Trackball Case Type C** housing reference;
- three 2 mm ceramic support balls/bearings as required by the housing design.

The PMW3360 remains on the breakout; Rev 1 does not integrate the optical sensor directly onto the keyboard PCB.

### Trackball electrical interface

Required physical interface:

- **1x7, 2.54 mm-pitch through-hole header** on the keyboard side;
- seven-conductor interface carrying:
  - CS;
  - MISO;
  - MOSI;
  - SCK;
  - MOTION position reserved but unused;
  - 3V3;
  - GND.

Rev 1 does **not** require the PMW3360 MOTION signal; polling is sufficient.

Frozen keyboard-side physical pin order entering Task 3:

| Pin | Signal |
| ---: | --- |
| 1 | CS |
| 2 | MISO |
| 3 | MOSI |
| 4 | SCK |
| 5 | NC / MOTION reserved |
| 6 | 3V3 |
| 7 | GND |

The checked-in Kivipallur breakout uses the same seven signals in the opposite numeric order. The verified mate is breakout pin `N` to keyboard pin `8-N`. Task 3 must preserve this physical pin order, keyboard-side F.Cu placement, and mating handedness; exact MCU GPIO ownership remains a Task-3 electrical decision.

### Trackball mechanical interface

Required:

- housing mounting screws belong to the **switchplate**, not the main PCB;
- nominal housing screw-pair spacing: **16 mm**;
- breakout/service opening reference envelope: **2 x 22 mm**;
- breakout/service path must remain accessible after assembly;
- trackball position must preserve controller clearance, TRRS clearance, and retained structural mounting axes;
- R32 / R33 and the right encoder are preserved geometry;
- R34 / SW22 / D22 is intentionally removed from the Rev-1 target;
- the Task-2D ball, housing, breakout, PMW-header, support-tongue, and structural-axis relationships are frozen canonical geometry.

The prior validated placement has been re-expressed parametrically in Ergogen. After Task 2D, changing those canonical relationships requires reopening Task 2.

### Structural interfaces and case

Required:

- preserve the previously verified **eight structural case/switchplate mounting axes**;
- stock **regular wired Konrad case** is the Rev-1 mechanical reference;
- left case should remain stock-compatible unless a generated replacement becomes necessary;
- right case is a local trackball derivative;
- use local shell relief around the trackball housing rather than moving preserved structural interfaces solely to avoid the stock-shell collision;
- retain the stock **1.5 mm switchplate thickness** as the Rev-1 reference stack-up.

Rev 1 is not based on the Bluetooth case.

### Firmware

Primary target: **QMK on RP2040**.

Required firmware capabilities:

- final matrix produced by the Task-2 retained-key set;
- split keyboard operation;
- left and right encoders;
- RGB matrix count matching **39 retained keys total (20 left / 19 right)**;
- PMW3360 on the right half;
- QMK split-pointing transport when the pointing side is not the USB master.

Current QMK documentation supports the PMW3360 driver and RP2040 split operation, including half-duplex transport and split pointing.

The following are tuning/configuration tasks, not hardware requirements:

- CPI;
- pointer rotation;
- axis inversion;
- lift-off behavior;
- scrolling behavior;
- acceleration;
- auto-mouse behavior;
- Vial keymap support.

---

## Stock KLOR feature classification

### Required

- KLOR 1.4 MX Konrad key geometry;
- MX hotswap switches;
- matrix diodes;
- per-key SK6812 Mini-E RGB;
- left rotary encoder;
- RP2040 Pro Micro-compatible controllers;
- TRRS split connection;
- reset capability / normal controller bootloader access;
- regular wired case geometry and structural interfaces where compatible.

### Intentionally removed from Rev 1

These features should not receive footprints, routing, keepouts, or firmware ownership unless a future requirements revision explicitly restores them:

- OLED;
- haptic feedback / DRV2605L;
- speaker/buzzer/audio/music;
- stock PAW3204 pointing-device circuit;
- general I2C accessory ownership inherited only for OLED/haptic/PAW3204;
- battery connector;
- battery operation;
- hardware power switch;
- Bluetooth / wireless requirement;
- ZMK as a Rev-1 deliverable;
- tenting-puck compatibility requirement;
- alternate KLOR layouts;
- break-away layout sections;
- reversible one-PCB-for-both-hands architecture;
- full-duplex split serial.

Removing these is deliberate: several also occupy GPIOs historically reused by the PMW3360 interface.

### Optional / deferred software behavior

These may be added without changing the Rev-1 hardware contract:

- Vial support;
- auto-mouse;
- high-resolution or layer-based scrolling behavior;
- CPI presets;
- pointer acceleration;
- orientation tuning;
- additional QMK user features that consume no new hardware interface.

---

## Task 3A electrical implementation

Task 3A freezes the Rev-1 electrical implementation in `ergogen/task3/task3a-electrical-contract.yaml`.

Selected controller: **0xCB Helios rev1.0**.

Frozen GPIO ownership:

- RGB: **GP25 through the Helios onboard 5 V level shifter**;
- half-duplex split serial: GP1;
- PMW SCK: GP2;
- PMW MOSI: GP3;
- PMW MISO: GP4;
- PMW CS: GP9;
- matrix rows: GP5, GP6, GP7, GP8;
- matrix columns: GP27, GP26, GP22, GP20, GP23, GP21;
- encoders: GP28/GP29, with right A/B reversed to preserve established direction semantics.

Power domains are explicit:

- RAW/5 V for SK6812 and split power;
- regulated 3.3 V from each Helios for the right-side PMW3360 breakout;
- common ground.

The historical GP0 RGB assignment is superseded. GP25 is used because Helios exposes it through an onboard 3.3 V → 5 V level shifter, matching the 5 V SK6812 power domain without adding a separate keyboard-PCB level shifter.

---

## Non-goals

Rev 1 is not intended to:

- redesign the KLOR finger/key ergonomics;
- become a low-profile Choc keyboard;
- reproduce Klorball35 geometry;
- support every stock KLOR optional peripheral;
- support wireless/battery operation;
- integrate PMW3360 directly on the main keyboard PCB;
- preserve the stock universal/reversible/multi-layout PCB architecture;
- optimize for arbitrary future variants at the cost of Rev-1 simplicity.

---

## Change control

Tasks 2–4 may choose implementation details, but they must not silently change this product contract.

**Exception for Task 2:** the exact right-thumb retained-key set, final total key count, and right-encoder retention are intentionally delegated to Task 2 because they depend on comparative trackball geometry. Once Task 2 locks that architecture, those decisions become part of this Rev-1 contract.

In particular, the following require an explicit requirements revision:

- changing the final Task-2 frozen right-thumb/key-count decision after Task 2 is complete;
- changing ball diameter;
- changing sensor family;
- replacing the breakout/housing architecture;
- restoring wireless/battery/OLED/haptic/audio;
- restoring a reversible or multi-layout PCB;
- changing the case family away from wired Konrad compatibility.
