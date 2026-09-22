# Task 3E Result — PMW3360 Routing

Status: **COMPLETE**

Task 3E routes the frozen Task 2 PMW3360 interface from U1 to the final Task 3D J4 location. The Task 3D mechanical geometry is unchanged.

## Routed interface

| J4 pin | Net | U1 ownership | Added segments | Added vias | Added length |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | PMW_CS | GP9 | 44 | 11 | 167.134 mm |
| 2 | PMW_MISO | GP4 | 27 | 2 | 98.456 mm |
| 3 | PMW_MOSI | GP3 | 37 | 4 | 126.112 mm |
| 4 | PMW_SCK | GP2 | 30 | 10 | 120.279 mm |
| 5 | NC / MOTION | unused | 0 | 0 | 0 |
| 6 | VCC | existing VCC rail | 1 | 0 | 2.526 mm |
| 7 | GND | ground | 5 | 0 | 10.679 mm |

The signal routes use 0.254 mm copper. VCC/GND additions use 0.381 mm copper. New vias use the board's existing compact 0.4 mm / 0.3 mm via convention.

The routing generator is deterministic and clearance-aware against the committed Task 3D geometry. Its route order is deliberately frozen because changing routing priority changes the available escape channels.

## Preservation boundary

Task 3E is additive only. It does not change any footprint, J4 placement, Edge.Cuts, existing Task 3D segment/via, zone definition, schematic, or split/RGB/matrix/encoder ownership.

The only new copper is on `GND`, `VCC`, `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, and `PMW_SCK`. J4.5 remains no-net and receives no routed copper.

## Verification

The Task 3E audit independently proves the exact Task 3D baseline, schematic preservation, exact preservation of all pre-existing copper/geometry, end-to-end connectivity for all four PMW signals, VCC/GND connectivity, an empty breakout pass-through, and MOTION remaining NC.

Final PCB Git blob:

```text
cdc63c3081881861bdcba8f0c6bc03a5b242baed
```

## DRC boundary

Task 3E proves the routing contract and source-level preservation. Full KiCad zone refill, integrated DRC, unexplained-unrouted review, and preservation classification remain the explicit Task 3F gate.

## Next

**Task 3F — preservation and integrated KiCad DRC audit.**
