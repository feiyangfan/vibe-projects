# KLOR Trackball — Ergogen Migration

## Goal

Build a KLOR 1.4 MX / Konrad trackball variant in which **design intent lives upstream of KiCad**.

The target architecture is:

```text
Ergogen source
  ├─ key/component points
  ├─ PCB/plate outlines
  ├─ mounting geometry
  ├─ trackball + breakout geometry
  └─ PCB footprint/net placement
        ↓
generated KiCad / mechanical geometry
        ↓
routing + validation
        ↓
fabrication outputs
```

Generated KiCad geometry is a derivative, not the source of truth. Do not reintroduce scripts that patch KiCad S-expressions by UUID or hard-coded object identity unless no upstream representation is possible.

## Migration reset

The previous implementation reached a routed Task 3E KiCad derivative, but it depended on direct KiCad mutation and preservation scripts. That implementation is intentionally retired from the active working tree for the Ergogen migration.

Nothing is lost: the complete pre-migration state is preserved in Git at commit:

`432ea630584c22dff2e9f5a596138dcc7602013f`

The previously routed derivative PCB blob was:

`cdc63c3081881861bdcba8f0c6bc03a5b242baed`

See `ergogen/reference-baseline.yaml` for the useful design facts carried forward as **reference evidence**, not as immutable implementation constraints.

## Active sources

- `ergogen/` — new active design workspace and future geometric source of truth.
- `klor1.4/` — stock KLOR 1.4 reference. Do not edit it to implement the trackball variant.
- `klorball35/` — Ergogen/Klorball/Kivipallur reference material.
- `Keyball 25mm Trackball Case Type C - 6719828/` — Type-C trackball housing source geometry.

Generated Klorball35 outputs, duplicate archives, the retired `PCB/konrad_trackball/` derivative, and the old task-specific mutation/audit framework are not part of the new active design.

## New roadmap

### Task 0 — Ergogen feasibility gate

Create the smallest validated KLOR-shaped Ergogen prototype:

- several exact Konrad key positions;
- one stock mounting pattern;
- MCU/TRRS/encoder reference points;
- one MX + RGB footprint;
- trackball and breakout reference geometry;
- generated KiCad PCB and plate outline.

**Gate:** regeneration is deterministic and the generated geometry can be compared numerically with the stock/reference KLOR sources.

### Task 1 — Requirements and reference reconstruction

Re-audit the stock KLOR, Klorball35/Kivipallur, Type-C housing, and firmware sources. Separate actual requirements from decisions that existed only because the old KiCad board was being patched.

### Task 2 — Canonical Ergogen geometry

Express the complete Konrad layout, structural holes, board outline, component datums, trackball assembly, breakout/service opening, connector placement, and plate geometry in Ergogen-controlled parameters.

### Task 3 — Generated electrical PCB

Generate the intended keyboard/trackball PCB structure: footprints, nets, matrix/RGB ownership, controller, encoder, split interface, PMW3360 connector, and power mapping.

### Task 4 — Routing pipeline

Choose and implement a regeneration-safe routing strategy. Manual KiCad work is acceptable only if it survives regeneration cleanly or is reproducibly replayed.

### Task 5 — Parametric switchplate and case

Drive the switchplate and case modification from the same canonical geometry. Ergogen owns 2D datums; a parametric CAD layer may own 3D solids.

### Task 6 — Integrated validation

Validate generated PCB, plate, case, housing, breakout, retained keys, encoder, structural mounts, clearances, and KiCad DRC.

### Task 7 — Firmware

Build the trackball-specific QMK variant from the final electrical contract.

### Task 8 — Fabrication and bring-up

Generate fabrication outputs, perform independent review, fabricate revision 1, and complete hardware bring-up.

## Rules for the migration

1. **One geometric authority.** Coordinates that affect PCB, plate, or case should be derived from the Ergogen model rather than copied manually between files.
2. **Reference is not authority.** Stock KLOR and the retired Task-3E derivative are comparison targets and evidence.
3. **Generated output is disposable.** A clean checkout must be able to reproduce generated geometry.
4. **No hidden manual geometry.** Any unavoidable downstream manual step must be documented and reproducible.
5. **Validate numerically.** Visual similarity is not sufficient for preserved KLOR geometry, mounting axes, or trackball interfaces.

## Current next step

**Task 0 — Ergogen feasibility gate.**
