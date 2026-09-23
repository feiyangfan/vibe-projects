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

**COMPLETE**

The active `config.yaml` reconstructs and regression-checks:

- all 20 fixed-Konrad stock key datums;
- right encoder;
- MCU and TRRS;
- nine stock PCB hole references;
- eight case/switchplate structural axes;
- the exact stock PCB Edge.Cuts as three source-derived closed paths;
- the stock switchplate outer perimeter from the checked-in SVG.

Passing evidence is recorded in `TASK2B_RESULT.md`.

### 2C — Trackball delta overlay

**NEXT**

Add parametrically:

- R34/SW22 suppression;
- 25 mm ball center;
- Type-C housing envelope;
- housing screw pair;
- breakout/service path;
- local PCB breakout notch;
- local switchplate service extension;
- PMW header placement envelope.

Every preserved Task-2B datum outside the trackball delta must remain numerically unchanged.

### 2D — Geometry freeze

Freeze the generated right-half geometry for Task 3 only after numeric preservation and clearance gates pass.

## Design rule

Every Task-2 feature should answer one of two questions:

1. **Is this stock geometry that must be preserved?**
2. **Is this the smallest explicit delta required by the trackball?**

If neither is true, it should not enter the canonical model.
