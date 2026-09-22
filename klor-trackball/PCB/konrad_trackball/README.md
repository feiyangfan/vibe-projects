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

The PCB remained the stock baseline through Task 3B. Task 3C subsequently synchronized the physical board.

See `../../design/task3/TASK3B_RESULT.md`.

## Task 3C PCB synchronization

Task 3C is complete.

The PCB now matches the authorized destructive portion of the Task 3B contract:

- `SW22` and `D22` are physically removed;
- the deleted-key local matrix copper is removed while `col1` and `row3` remain distinct;
- `RX` is retired and `J1.3` is physically no-net;
- `J1.4/TX` remains intact;
- U1 owns `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- SW13 DOUT and SW14 DIN are one PCB net with a permanent B.Cu splice;
- J4 exists with the frozen 1×7 keyboard-side pin contract.

Task 3C left J4 staged off-board and kept stock Edge.Cuts unchanged.

See `../../design/task3/TASK3C_RESULT.md`.

## Task 3D connector and pass-through

Task 3D is complete.

- J4 is final-placed on `F.Cu` at `(147.724665,142.367997)`, rotation 0°.
- Its row midpoint is `(147.724665,134.747997)`, +4.613622 mm X from the locked breakout guide center.
- The board has an actual open 2 mm edge notch matching the locked 2×22 mm service envelope.
- A local +X tongue supports the J4 through-holes.
- VCC and the RGB bypass are locally rerouted only where required by the notch/header.
- At the end of Task 3D, J4-to-U1 PMW routing was intentionally incomplete; Task 3E completes it below.

See `../../design/task3/TASK3D_RESULT.md`.

## Task 3E PMW3360 routing

Task 3E is complete.

- `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, and `PMW_SCK` are routed from U1 to J4.
- J4.6 connects to the existing `VCC` rail.
- J4.7 connects to `GND`.
- J4.5 / MOTION remains NC.
- The routing is additive; Task 3D connector/pass-through geometry and all pre-existing copper are preserved.

See `../../design/task3/TASK3E_RESULT.md`.

**Next: Task 3F — preservation and integrated DRC audit.**

## Zone-fill cache policy

Generated `filled_polygon` cache data is not committed. The Task 3E board remains directly accessible through repository tooling. Refill zones in KiCad before DRC/fabrication, then strip cached fills again before committing.
