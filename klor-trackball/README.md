# KLOR Trackball — Parametric Ergogen Migration

## Product goal

Build a **fabrication-ready KLOR 1.4 MX / Konrad split keyboard variant with a 25 mm PMW3360 trackball integrated into the right thumb area**, while preserving the KLOR characteristics we intentionally keep and making the modified design reproducible and easy to adjust.

The intended product direction is:

- base keyboard: **KLOR 1.4, MX/full-height, Konrad layout**;
- trackball: **25 mm**, on the right half;
- sensor: **PMW3360**;
- breakout architecture: **Kivipallur-style PMW3360 breakout**;
- housing reference: **Keyball 25 mm Trackball Case Type C**;
- left rotary encoder retained;
- right-thumb key retention and right-encoder retention to be decided by comparative Task-2 geometry;
- historical comparison baseline: **39 keys total — 20 left / 19 right**, removing R34;
- complete deliverable: **PCB + switchplate + case + firmware + fabrication outputs**.

Those details are now frozen for Rev 1 in [`REQUIREMENTS.md`](REQUIREMENTS.md). Task 1 explicitly classified stock KLOR features as required, optional/deferred, or intentionally removed.

## Engineering goal

Ergogen is not the product goal. It is the mechanism used to prevent the project from becoming a collection of difficult manual KiCad and CAD edits.

A meaningful design change should primarily be:

```text
change parameters
    ↓
regenerate
    ↓
validate
```

rather than:

```text
edit KiCad objects
    ↓
repair traces / outlines / UUID-dependent scripts
    ↓
manually synchronize CAD
    ↓
audit unrelated geometry
```

The target architecture is:

```text
canonical design parameters
          ↓
       Ergogen
          ↓
 shared 2D geometry + PCB placement intent
   ┌──────────┼──────────────┐
   ↓          ↓              ↓
  PCB      switchplate    CAD inputs
   ↓          ↓              ↓
 KiCad      DXF/STEP     parametric case
   └──────────┼──────────────┘
              ↓
         validation
              ↓
         fabrication
```

Generated KiCad geometry is a derivative, not the primary geometric source of truth. Avoid UUID-based or object-identity-based KiCad mutation unless an upstream representation is genuinely impossible.

## Core project principles

1. **One geometric authority.** Geometry shared by PCB, switchplate, case, and trackball interfaces should be derived from the same upstream model.
2. **Parameters over copied coordinates.** Relationships such as trackball position, housing screw pattern, breakout offset, and key geometry should be expressed parametrically wherever practical.
3. **Generated output is disposable.** A clean checkout should be able to reproduce generated geometry.
4. **Reference is not authority.** Stock KLOR, Klorball35, and the retired Task-3E board are evidence and comparison targets, not implementation constraints.
5. **No hidden manual geometry.** Any unavoidable downstream manual operation must be documented and reproducible.
6. **Validate numerically.** Visual similarity is not sufficient for preserved layout geometry, mounting axes, PCB interfaces, or mechanical clearances.
7. **A working file is not enough.** A task is complete only when its result can be reproduced from upstream source without substantial repeated manual work.

---

## Reference sources

### KLOR 1.4

`klor1.4/` is the stock KLOR 1.4 reference and should remain unmodified as upstream evidence.

It provides the reference MX/Konrad PCB, firmware, case, switchplate, fabrication constraints, component placement, and structural interfaces.

### Klorball35 / Kivipallur

`klorball35/` is a design reference, not the target keyboard.

It demonstrates an Ergogen-driven split-keyboard workflow plus a PMW3360/Kivipallur trackball architecture, but it uses different key geometry, Choc switches, and a different overall layout.

Useful concepts should be reused; its geometry should not be copied wholesale.

### Trackball housing

`Keyball 25mm Trackball Case Type C - 6719828/` contains the housing STEP/STL reference used for the 25 mm trackball mechanical interface.

### Retired implementation

The previous implementation reached a routed Task 3E KiCad derivative using direct KiCad mutation and preservation scripts.

That implementation is intentionally retired from the active working tree, but remains recoverable from Git:

- pre-migration commit: `432ea630584c22dff2e9f5a596138dcc7602013f`;
- previous Task-3E PCB blob: `cdc63c3081881861bdcba8f0c6bc03a5b242baed`;
- summarized regression evidence: `ergogen/reference-baseline.yaml`.

The old implementation is useful for comparison and recovered engineering evidence. It should not dictate the architecture of the new design.

---

# Sequential roadmap

The dependency order is:

```text
Task 0  generation feasibility
   ↓
Task 1  product requirements
   ↓
Task 2  canonical geometry
   ↓
Task 3  electrical PCB generation
   ↓
Task 4  regeneration-safe routing
   ↓
Task 5  parametric switchplate
   ↓
Task 6  parametric right case
   ↓
Task 7  full digital integration
   ↓
Task 8  firmware
   ↓
Task 9  fabrication + hardware bring-up
```

## Task 0 — Prove the generation architecture

**Status: COMPLETE**

Before rebuilding the complete keyboard, prove that the toolchain works end to end on a small, real slice of the design.

The feasibility prototype should include:

- several real KLOR/Konrad switch positions;
- representative stock mounting points;
- MCU/TRRS/encoder reference points;
- trackball and breakout reference datums;
- a generated PCB outline;
- a generated switchplate outline;
- at least one real switch footprint;
- at least one RGB footprint;
- generated KiCad output.

Validation should compare generated coordinates numerically with the stock KLOR source rather than relying on screenshots or visual alignment.

**Completion gate**

- Ergogen runs from a clean checkout.
- Two clean generation passes are deterministic.
- Selected stock KLOR positions match numerically.
- Trackball and breakout reference datums match the intended regression reference.
- A KiCad PCB is generated.
- A plate geometry output is generated.
- The process is simple enough that extending the model is clearly preferable to returning to manual KiCad surgery.

Task 0 proves the **workflow**, not the final production geometry.

---

## Task 1 — Freeze product requirements

**Status: COMPLETE**

Define the finished keyboard independently of decisions made only to accommodate the old patched PCB.

Re-audit:

- stock KLOR 1.4;
- Konrad layout;
- Klorball35/Kivipallur;
- Type-C trackball housing;
- stock firmware;
- fabrication requirements.

Explicitly classify stock functionality as:

- **required**;
- **optional**;
- **intentionally removed**.

This includes:

- fixed versus geometry-dependent product decisions;
- right-thumb/trackball decision criteria;
- right rotary encoder trade-space;
- controller;
- TRRS/split transport;
- RGB;
- OLED;
- haptic;
- audio;
- stock pointing-device support;
- battery/power-switch support;
- tenting-puck support;
- reset switch;
- other reversible-board features.

**Completion gate**

A short authoritative requirements document exists, and any geometry-dependent product decision is explicitly bounded and assigned to Task 2 before Task 3 may begin.

---

## Task 2 — Reconstruct the complete KLOR/Konrad geometry in Ergogen

**Status: IN PROGRESS**

Task 2 begins with a minimal-change study before full reconstruction. The selected implementation baseline is to remove R34/SW22/D22 only, retain R32/R33 and the right encoder, preserve all structural interfaces, and keep PCB/plate/case changes local to the trackball region. See `ergogen/task2/MINIMAL_CHANGE_STUDY.md`.

Build the actual canonical geometric model.

Before freezing the final right-half geometry, compare the right-thumb/trackball trade-space. At minimum include the historical R34-only + right-encoder baseline and alternatives that remove additional thumb controls and/or the right encoder if they materially improve trackball reach, clearance, or serviceability.

Task 2 must lock the final retained subset of R32/R33/R34, total key count, and right-encoder decision before Task 3.

Model:

- every retained switch center and rotation;
- thumb cluster;
- encoder;
- MCU;
- TRRS;
- structural mounting holes;
- PCB perimeter;
- switchplate perimeter;
- switch cutouts;
- relevant keepout/envelope geometry;
- trackball center;
- trackball housing screw pattern;
- breakout/service path;
- trackball connector position.

First prove that the Ergogen model reproduces the stock KLOR geometry that should remain unchanged.

Then add the trackball modification.

Prefer relationships such as:

```text
trackball position
housing screw offsets
breakout offset
connector offset
```

over separately maintained absolute coordinates.

**Completion gate**

The generated canonical geometry numerically reproduces all intentionally preserved KLOR/Konrad geometry, expresses the trackball system parametrically, and freezes the final right-thumb key set / key count / right-encoder architecture for Task 3.

---

## Task 3 — Establish production footprints and generate the electrical PCB

Turn the geometric model into a real electrical PCB definition.

Implement or validate production footprints for all retained hardware, including as applicable:

- MX hotswap switches;
- SK6812 Mini-E RGB;
- diodes;
- RP2040 / Pro Micro-compatible controller;
- TRRS;
- EC11 encoder;
- reset/power components;
- PMW3360 connector;
- mounting hardware.

Encode the electrical model:

- key matrix;
- RGB chain;
- split transport;
- encoder;
- PMW3360 SPI;
- power;
- removed thumb-key circuit;
- final GPIO ownership.

**Completion gate**

Ergogen generates a complete, electrically coherent **unrouted production-intent PCB** from source.

---

## Task 4 — Build a regeneration-safe routing pipeline

This task determines whether the migration actually solves the maintenance problem.

Answer:

> What happens to routing after the Ergogen configuration changes?

Prefer, in order:

1. deterministic/generated routing where practical;
2. replayable routing logic based on nets and geometry;
3. constrained downstream KiCad routing only where it can survive or be reproduced after regeneration.

Do not recreate the previous architecture of large scripts that search for exact KiCad UUIDs or object identities.

Treat different routing classes independently where appropriate:

- matrix;
- RGB;
- power;
- ground planes;
- split transport;
- encoder;
- PMW3360 SPI;
- trackball connector.

**Completion gate**

Make at least one meaningful upstream geometric change, regenerate, and restore a valid routed PCB without manually rebuilding the affected routing.

---

## Task 5 — Build the parametric switchplate

The switchplate should consume the same canonical geometry as the PCB.

Generate or parametrically construct:

- MX cutouts;
- structural mounting holes;
- trackball housing mounting holes;
- housing clearance;
- breakout/service opening;
- outer plate perimeter.

Ergogen may own the 2D geometry while another CAD tool owns downstream 3D solids.

The critical rule is:

> Trackball and mounting coordinates must not be independently retyped into CAD.

**Completion gate**

PCB and switchplate mounting/trackball interfaces remain aligned automatically when the shared upstream geometry changes.

---

## Task 6 — Build the parametric right case

Create a reproducible editable right-case derivative.

The stock regular right case is a reference, but the new case workflow must be editable and parameter driven.

Preserve or intentionally reproduce:

- KLOR external/interface geometry that matters;
- structural mounting axes;
- PCB/plate stack-up;
- required wall thickness;
- assembly/service access.

Add:

- trackball housing envelope;
- local shell relief;
- breakout access;
- required connector clearances.

The left case should remain stock unless Task 1 identifies a reason to regenerate it.

**Completion gate**

A change to relevant upstream trackball geometry can propagate into the case without manually relocating the associated relief/interface features.

---

## Task 7 — Full digital integration and validation

Assemble the generated system digitally:

```text
PCB
+ switches
+ encoder
+ controller
+ switchplate
+ right case
+ trackball housing
+ 25 mm ball
+ Kivipallur breakout
```

Validate:

- physical collisions;
- keycap clearances;
- trackball finger access;
- housing clearance;
- mounting screw access;
- breakout insertion/removal path;
- connector accessibility;
- case wall thickness;
- PCB-to-case clearance;
- KiCad DRC;
- unrouted nets;
- RGB chain continuity;
- power and grounding assumptions.

**Completion gate**

The complete mechanical/electrical design is fabrication-ready in the digital model.

---

## Task 8 — Firmware

Implement firmware only after the hardware contract is stable.

Implement:

- final key matrix;
- final RGB count and map;
- encoder;
- split transport;
- PMW3360 SPI;
- right-half pointing-device ownership;
- CPI;
- pointer orientation;
- scrolling behavior;
- optional auto-mouse behavior.

Recommended bring-up order:

```text
matrix
→ split
→ encoder
→ RGB
→ SPI communication
→ PMW3360 motion
→ pointer tuning
```

**Completion gate**

Firmware ownership and pin assignments exactly match the generated PCB, and the complete configuration builds reproducibly.

---

## Task 9 — Fabrication package and first hardware revision

Generate the complete release package from a clean checkout:

- KiCad PCB;
- Gerbers and drills;
- BOM/assembly data where applicable;
- switchplate DXF/STEP/STL or equivalent fabrication outputs;
- case STEP/STL;
- firmware;
- assembly documentation.

Independently inspect fabrication outputs before ordering.

Recommended physical bring-up order:

```text
continuity / shorts
→ power rails
→ controller
→ key matrix
→ split
→ RGB
→ encoder
→ PMW3360
→ final pointer tuning
```

**Completion gate**

Revision 1 hardware is fabricated, assembled, electrically validated, and mechanically validated.

---

## Active workspace

`ergogen/` is the active design workspace.

Expected structure:

```text
ergogen/
  config.yaml
  footprints/
  scripts/
  reference-baseline.yaml
  generated/          # reproducible / ignored
```

Generated output should never become the only place where design intent exists.

## Current work

**Task 2C — Overlay the minimal trackball delta.**

Tasks 2A and 2B are complete. The minimal-change baseline is documented in `ergogen/task2/MINIMAL_CHANGE_STUDY.md`, and the passing stock-geometry regression is recorded in `ergogen/task2/TASK2B_RESULT.md`.
