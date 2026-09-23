# Task 2 — Canonical Geometry Foundation

Task 2 is the foundation of the production design.

The objective is not to recreate every stock KLOR artifact from scratch. The objective is to identify the **smallest stock-to-trackball delta**, then encode the preserved geometry and that delta in one reproducible canonical model.

## Phases

### 2A — Minimal-change study

**COMPLETE**

See:

- `MINIMAL_CHANGE_STUDY.md`
- `minimal-change-baseline.yaml`

Selected implementation baseline:

- remove R34/SW22/D22 only;
- retain R32/R33;
- retain the right encoder;
- start from the previously validated 25 mm Type-C placement;
- preserve the stock PCB/plate/case structure outside local trackball interfaces.

This selection is based on minimum product/CAD/PCB change. It is not a claim that more aggressive thumb-key removal could never produce a different ergonomic preference.

### 2B — Stock geometry reconstruction

**IN PROGRESS**

Build the preserved KLOR/Konrad geometry in Ergogen and regress it numerically against stock sources. The active `config.yaml` now reconstructs the 20 fixed-Konrad key datums, encoder, MCU/TRRS, nine stock PCB hole references, eight case/switchplate structural axes, the exact stock PCB Edge.Cuts (three closed chains), and the stock switchplate outer perimeter.

### 2C — Trackball delta overlay

Add the trackball, housing screws, breakout/service path, and local PCB/plate modifications as parameters relative to the preserved stock geometry.

### 2D — Geometry freeze

Freeze the generated right-half geometry for Task 3 only after numeric preservation and clearance gates pass.

## Design rule

Every Task-2 feature should answer one of two questions:

1. **Is this stock geometry that must be preserved?**
2. **Is this the smallest explicit delta required by the trackball?**

If neither is true, it should not enter the canonical model.
