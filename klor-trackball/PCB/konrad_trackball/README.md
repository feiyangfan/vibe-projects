# Konrad Trackball KiCad Derivative

This directory is the editable KiCad source for the KLOR 1.4 MX Konrad right-hand PMW3360 trackball derivative.

## Task 3A baseline

Task 3A creates this project as a non-destructive fork of the stock KLOR 1.4 KiCad project.

Baseline rules:

- Stock source remains under `klor-trackball/klor1.4/PCB/klor1_4/` and must not be edited.
- The derivative project basename is `konrad_trackball`.
- `konrad_trackball.kicad_pcb` and `konrad_trackball.kicad_sch` begin byte-identical to the stock `klor1_4` board and schematic.
- The stock design-rules file and local KLOR symbol/footprint libraries are copied unchanged.
- The only intentional content difference in the baseline project file is `meta.filename`, changed from `klor1_4.kicad_pro` to `konrad_trackball.kicad_pro`.
- Stock Gerbers are intentionally not copied. Fabrication outputs must be regenerated from the completed derivative later.
- No Task 2 electrical changes are implemented in Task 3A. Those begin with Task 3B.

Canonical Task 3 plan and gates are documented in `../../design/task3/README.md`.
