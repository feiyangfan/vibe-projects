# Task 3B Result — Production Footprint Qualification

## Status

**PASS — Task 3B is complete and the Rev-1 production footprint set is qualified.**

Task 3B converts the Task-3A electrical architecture into a locally controlled Ergogen footprint library. It does not generate either production board yet and does not route copper.

## Passing source state

Branch:

`klor-trackball/task3b-footprints`

Passing head:

`74767082a2ba19d2eced5e8154d03b150c97ee58`

GitHub Actions:

- workflow: `KLOR Task 3B - production footprints`
- run ID: `35837381610`
- job ID: `107103979036`
- conclusion: **success**

Qualification artifact:

- name: `klor-task3b-footprint-fixture`
- artifact ID: `10739732940`
- SHA-256: `6dfbe6f4efb9e3b7e0826a778d046becb8fe6698bc09c3ca4e85e5e41f9f7100`

The workflow also re-runs Task 2B, 2C, 2D, and Task 3A before accepting the footprint library.

## Qualified local modules

The production modules are checked in under `ergogen/footprints/`:

| Module | Production use |
| --- | --- |
| `klor_key` | MX hotswap + SK6812MINI-E |
| `klor_diode` | 1N4148W / SOD-123 |
| `helios_host` | 0xCB Helios rev1.0 host/socket |
| `klor_trrs` | MJ-4PP-9 TRRS |
| `klor_ec11` | EC11E encoder + push switch |
| `klor_reset` | Alps SKRTLAE010 reset |
| `pmw_header` | frozen 1×7 PMW3360 interface |
| `mounting_hole` | stock M3/M2 PCB holes |

Tasks 3C/3D must consume these local modules rather than substituting generic Ergogen production footprints.

## Non-reversible production policy

Stock KLOR was designed around reversible/multi-layout hardware. Rev 1 deliberately uses separate left and right boards.

Task 3B therefore preserves source-qualified geometry needed by the selected component side while deleting reversibility-only duplication.

This is deliberate simplification, not geometry drift.

### MX hotswap + SK6812MINI-E

Source:

`KLOR.pretty/SK6812MINI_and_cherry.kicad_mod`

Qualified behavior:

- preserve stock switch center and stabilizer geometry;
- preserve selected-side Kailh hotswap pad centers/sizes;
- preserve selected-side socket pin holes;
- preserve selected-side SK6812 Mini-E pad centers/sizes;
- preserve the reverse-mount LED Edge.Cuts opening;
- remove the duplicate opposite-side socket and RGB lands.

Electrical pad contract:

| Pad | Function |
| ---: | --- |
| 1 | RGB DOUT |
| 2 | GND |
| 3 | RGB DIN |
| 4 | RAW_5V |
| 5 | matrix column |
| 6 | switch-to-diode |

Both F- and B-side variants are qualification-tested. Production boards can explicitly choose the appropriate side without restoring reversible duplication.

### SOD-123 diode

The stock footprint used small plated holes to make the SOD-123 lands reversible.

Rev 1 preserves:

- pad centers: ±1.7 mm;
- pad size: 1.8 × 1.5 mm;
- pad numbering: pad 1 row side, pad 2 switch side.

The production footprint converts those lands to ordinary single-side SMD pads with no through drill.

### Helios host

Controller:

**0xCB Helios rev1.0**, upstream commit:

`e1a25eb5e4b1bcb25e13dcb18bd6e841dcf7be11`

The standard Helios inner rows align to the frozen stock KLOR U1 Pro-Micro hole grid without moving U1.

The host exposes:

- Helios pads 2–13 on the left standard row;
- Helios pads 30–19 on the right standard row;
- extra Helios pad **32** for the onboard level-shifted GP25 RGB output.

The extra pad-32 host contact is at:

```text
host-local = (-6.275, 10.63) mm
drill      = 1.0 mm
pad        = 1.7 × 1.7 mm
```

Helios pads 1, 31, 33, and 34 are intentionally not hosted because Rev 1 has no electrical use for them.

The source-derived Helios body envelope remains compatible with the frozen U1 position. The conservative nearest retained-key envelope clearance is approximately **6.462 mm to SW6**.

Task 3B therefore does **not** reopen the frozen U1 position.

### TRRS

Source:

`KLOR.pretty/MJ-4PP-9.kicad_mod`

F- and B-side mounting variants retain the corresponding stock pad/stabilizer geometry while instantiating only one physical side per non-reversible board.

Frozen pin contract:

| Pin | Net |
| ---: | --- |
| 1 | RAW_5V |
| 2 | GND |
| 3 | NC |
| 4 | SPLIT_DATA |

### EC11

The stock EC11E footprint geometry is retained without electrical or mechanical reinterpretation:

- A/B/C rotary pins;
- S1/S2 push pins;
- mounting tabs.

### Reset

The stock reversible SKRTLAE010 footprint uses small plated holes to duplicate lands across sides.

Rev 1 preserves all land centers/sizes but emits a conventional single-side SMD variant:

- pad 1 = RESET;
- pad 2 = GND;
- mounting lands retained;
- reversible microdrills removed.

### PMW header

The footprint directly implements the frozen Task-2D physical connector contract:

- 1×7;
- 2.54 mm pitch;
- F.Cu;
- 1.0 mm drill;
- 1.7 mm pad;
- pin 5 remains electrically NC.

Pin order:

| Pin | Net |
| ---: | --- |
| 1 | PMW_CS |
| 2 | PMW_MISO |
| 3 | PMW_MOSI |
| 4 | PMW_SCK |
| 5 | NC / MOTION |
| 6 | V3V3 |
| 7 | GND |

### PCB mounting holes

Qualified from stock PCB references:

- MH1–MH8: 3.2 mm M3 NPTH;
- MH9: 2.2 mm M2 NPTH.

No copper is assigned to these holes.

## Qualification fixture

Task 3B adds a dedicated generated KiCad fixture:

`task3b_footprint_fixture.kicad_pcb`

It instantiates all production footprint classes, including F/B variants where relevant, solely for deterministic generation and pad-geometry regression.

It is not a production keyboard PCB.

## Validation result

The passing validator proves:

- all eight local footprint modules exist;
- MX hotswap/SK6812 selected-side geometry derives from stock KLOR;
- SOD-123 production land geometry is preserved while reversible drills are removed;
- Helios standard rows align with the stock U1 grid;
- Helios pad 32 is exposed at the audited location;
- frozen U1 placement still clears retained keys;
- F/B TRRS variants derive from stock source geometry;
- EC11 geometry remains stock-derived;
- reset land geometry survives de-reversibilization;
- PMW header matches the frozen Task-2D physical/electrical contract;
- stock M3/M2 hole drills are preserved;
- generation is deterministic;
- all upstream Task-2 and Task-3A gates still pass;
- routing remains outside Task 3.

A source file stores one F-side socket hole at Y `-2.540001` mm while the nominal qualified geometry uses `-2.54` mm. The validator treats this as the source's one-micron representation noise while keeping source matching at a 2e-6 mm tolerance.

## Task 3C handoff

Task 3C may now generate the left production-intent PCB using:

- frozen Task-2 geometry;
- frozen Task-3A nets/GPIO ownership;
- the Task-3B local footprint library.

Task 3C should not need to make new footprint or electrical-architecture decisions.

## Next

Proceed to **Task 3C — generate the left production-intent unrouted PCB**.
