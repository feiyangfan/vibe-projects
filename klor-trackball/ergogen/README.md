# Ergogen Workspace

This directory is the active workspace for the KLOR trackball migration.

## Intent

Ergogen will become the canonical owner of 2D design geometry and PCB placement intent. The migration is deliberately restarting from reference sources rather than translating the retired KiCad mutation scripts line-by-line.

Expected long-term structure:

```text
ergogen/
  config.yaml                 # canonical Ergogen model
  footprints/                 # project-specific Ergogen footprints/plugins
  scripts/                    # deterministic generation/validation helpers
  reference-baseline.yaml     # pre-migration evidence only
  generated/                  # ignored/reproducible outputs
```

Only `config.yaml` and source helpers should become authoritative. `generated/` must remain reproducible.

## Bootstrap config

`config.yaml` is intentionally minimal. It establishes the source location and the Ergogen engine family already used by the checked-in Klorball35 reference. Task 0 will add the first validated KLOR points, outlines, and PCB output.

Do not copy the existing Klorball35 layout wholesale. It is a useful Ergogen example and trackball reference, but the target keyboard is KLOR 1.4 MX / Konrad.

## Reference policy

`reference-baseline.yaml` records the useful facts from the retired implementation. These values are **comparison targets**, not automatically locked requirements. Task 0/1 may retain, derive differently, or reject them based on the actual stock/reference geometry.

The complete old implementation remains available at Git commit `432ea630584c22dff2e9f5a596138dcc7602013f`.
