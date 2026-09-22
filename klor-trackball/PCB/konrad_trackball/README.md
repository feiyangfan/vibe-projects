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

## Task 3B schematic contract

Task 3B is complete.

The derivative schematic now owns the frozen Task 2 electrical interface:

- `SW22` and `D22` are removed from the schematic;
- RGB is bypassed logically as `SW13 DOUT → SW14 DIN`;
- U1-side nets are `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- `J4` is the 1×7 PMW3360/Kivipallur keyboard-side connector:
  `1=PMW_CS, 2=PMW_MISO, 3=PMW_MOSI, 4=PMW_SCK, 5=NC, 6=VCC, 7=GND`;
- `J1.3` is NC and `J1.4/TX` remains the active split connection;
- `J2`, `OLED1`, and `BZ1` are DNP for revision 1.

The PCB remains the stock baseline intentionally. Do not interpret the still-present SW22/D22 PCB footprints or stock copper as the final board.

**Next: Task 3C** synchronizes this schematic contract onto the PCB and performs the authorized destructive physical edits.

See `../../design/task3/TASK3B_RESULT.md`.

## Zone-fill cache policy

This derivative follows the repository-wide PCB normalization policy: generated `filled_polygon` cache data is not committed. Refill zones in KiCad before DRC or fabrication, then strip cached fills again before committing.
