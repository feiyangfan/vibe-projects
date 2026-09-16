# KLORBALL35

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/images/klorball35-layout-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="/docs/images/klorball35-layout-light.svg">
  <img alt="Klorball35 layout" src="/docs/images/klorball35-layout-light.svg">
</picture>

**Klorball35** is a 35-key, column-staggered, low-profile split keyboard with an integrated optical trackball. It's derived from [KLOR](https://github.com/GEIGEIGEIST/KLOR) and [Keyball](https://github.com/Yowkees/keyball),  built with [Kivipallur](https://github.com/dr3san/Kivipallur) as a starting point in [Ergogen](https://ergogen.cache.works/), and designed around Kailh Choc V1 switches, an [0xCB Helios](https://github.com/0xCB-dev/0xCB-Helios) (RP2040) controller per half, and a PixArt **PMW3360** sensor on the right hand.

***

## LAYOUT

Each half carries a 5-column × 3-row main matrix plus a 3-key (left) and 2-key (right)thumb cluster. The right hand gives up one key to make room for the trackball, so the two halves are **18 (left) + 17 (right) = 35 keys**.

- Column-staggered, splayed columns with per-column stagger/splay tuning
- Kailh Choc V1 (low-profile) switches, 18 × 17 mm spacing
- TRRS jack for the inter-half connection
- M2 mounting holes and a matching FR4 switchplate per half
- PMW3360 optical trackball on the right half via the *Kivipallur* breakout

***

## IMAGES

![Klorball35 fully assembled](/docs/images/klorball_full.jpg)

▲ The assembled Klorball35.

![Klorball35 mounted on a tripod](/docs/images/klorball_tripod.jpg)

▲ Mounted on a tripod.

![Klorball35 right-half trackball assembly](/docs/images/klorball_right_trackball_assembly.jpg)

▲ The right-half trackball assembly.

***

## PCB

[`kicad/`](/kicad/) holds the KiCad 9 projects:

| Project | Description |
| --- | --- |
| [`klorball35_left`](/kicad/klorball35_left/) | Left-half PCB + schematic |
| [`klorball35_right`](/kicad/klorball35_right/) | Right-half PCB + schematic (trackball) |
| [`klorball35_plate_left`](/kicad/klorball35_plate_left/) | Left FR4 switchplate |
| [`klorball35_plate_right`](/kicad/klorball35_plate_right/) | Right FR4 switchplate |
| [`Kivipallur_PMW3360_breakout`](/kicad/Kivipallur_PMW3360_breakout/) | PMW3360 trackball sensor breakout |

Shared footprint and symbol libraries (`Keebio-Parts.pretty`, `keyswitches.pretty`, `Helios.pretty`, `Mounting_Hole.pretty`, etc.) live alongside the projects.

Manufacturing **Gerbers** are in [`gerbers/`](/gerbers/):

- `GERBER-klorball35_left.zip` / `GERBER-klorball35_right.zip` — main PCBs
- `GERBER-klorball35_plate_left.zip` / `GERBER-klorball35_plate_right.zip` — FR4 switchplates
- `GERBER-Kivipallur_PMW3360_breakout.zip` (+ BOM and CPL CSVs) — trackball breakout

***

## SOURCE

The whole board is generated from a single Ergogen definition, [`config.yml`](/config.yml) (Ergogen `4.2.1`). Regenerate the outlines and PCB scaffolds with:

```sh
ergogen config.yml --svg -o output
```

Outputs land in [`output/`](/output/) (`outlines/` as DXF/SVG and `pcbs/` as KiCad files), which are then finished by hand in KiCad.

***

## SWITCHPLATE

A matching FR4 switchplate is generated for each half (`klorball35_plate_left` / `klorball35_plate_right`, with Gerbers in `gerbers/`). The plate outline is shared with the main board; only the key cutouts and M2 screw holes differ.

***

## TRACKBALL

The right half integrates a PixArt **PMW3360DM-T2QU** optical sensor on the *Kivipallur* breakout ([`kicad/Kivipallur_PMW3360_breakout`](/kicad/Kivipallur_PMW3360_breakout/)). It connects to the right-hand Helios over SPI through the breakout slot in the PCB.

***

## FIRMWARE

Each half runs on an [0xCB Helios](https://github.com/0xCB-dev/0xCB-Helios) RP2040 controller (Pro Micro-compatible footprint), so the board can run **QMK** or **ZMK**. A dedicated Klorball35 firmware config isn't published yet; the stock [KLOR QMK config](https://github.com/GEIGEIGEIST/qmk-config-klor) and [KLOR ZMK config](https://github.com/GEIGEIGEIST/zmk-config-klor) are good starting points, with the matrix and the PMW3360 trackball wired up to match this board.

***

## CREDITS

- **[KLOR](https://github.com/GEIGEIGEIST/KLOR)** by [GEIGEIGEIST](https://github.com/GEIGEIGEIST) — One of the best keyboards I have used.
- **[0xCB Helios](https://github.com/0xCB-dev/0xCB-Helios)** by [0xCB](https://github.com/0xCB-dev) — the RP2040 controller.
- **[Ergogen](https://github.com/ergogen/ergogen)** by [MrZealot](https://github.com/mrzealot) — the keyboard generator.
- **[Kivipallur](https://github.com/dr3san/Kivipallur)** by [dr3san](https://github.com/dr3san) — the board that got this project started.
- **[25mm Trackball Housing](https://www.thingiverse.com/thing:6719828)** by [kepeo](https://www.thingiverse.com/kepeo/designs)
- The **Keebio** footprint library and the PixArt PMW3360 breakout that the Kivipallur design is based on.

Built by **danbowles**.
