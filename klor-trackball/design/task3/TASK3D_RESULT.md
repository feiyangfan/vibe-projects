# Task 3D Result — Connector + Fabricated Pass-Through

Status: **COMPLETE**

Task 3D finalizes the mechanical PCB interface for the Kivipallur PMW3360 breakout. It does not route the PMW signals; that remains Task 3E.

## Final geometry

Locked breakout/pass-through datum in KLOR Gerber/Excellon coordinates:

```text
(143.111, -134.748) mm
```

Equivalent KiCad PCB center used by the board:

```text
(143.111043, 134.747997) mm
```

The fabricated interface is an **open 2 mm-wide edge notch** following the Klorball35 2×22 mm service envelope. Because the locked envelope intersects the stock lower board edge, the correct manufacturable interpretation is an open notch rather than a closed internal slot.

A local +X support tongue is added for J4. Its limiting edges are:

```text
notch left X  = 142.111043
notch right X = 144.111043
notch top Y   = 123.747997
tongue right  = 150.000000
tongue bottom = 144.250000
```

The original lower-edge cubic is truncated exactly at the notch wall; all other stock Edge.Cuts remain unchanged.

## J4 final placement

J4 stays on `F.Cu` with the Task 2C orientation and frozen pin contract.

```text
footprint anchor / pin 1: (147.724665, 142.367997)
rotation:                 0 deg
row midpoint:             (147.724665, 134.747997)
guide-to-row offset:      +4.613622 mm X
```

The row is parallel to global Y. Under the locked KiCad→Gerber reflection, pin 1 is the negative-Y end and pin 7 is the positive-Y end.

Pin order is unchanged:

| Pin | Net |
| ---: | --- |
| 1 | PMW_CS |
| 2 | PMW_MISO |
| 3 | PMW_MOSI |
| 4 | PMW_SCK |
| 5 | NC / MOTION |
| 6 | VCC |
| 7 | GND |

## Required local copper accommodation

The fabricated notch and final header overlap a small amount of Task 3C copper, so Task 3D makes only the mechanically required local reroutes:

- VCC is wrapped around the notch with 0.381 mm F.Cu traces;
- one VCC layer-change via is moved to `(145.3, 133.81)`;
- the Task 3C RGB bypass is shortened to the already-retained right-side endpoints:
  `(151.129969,128.715031) → (151.705,130.22)` on B.Cu.

No PMW signal is routed to J4 in 3D.

## Verification

The Task 3D audit proves:

- exact Task 3C PCB baseline and Task 3B schematic are preserved as dependencies;
- J4 is the only footprint whose placement changes;
- all unrelated Edge.Cuts, traces, vias, footprints, and zone definitions remain exact;
- the nominal 2×22 mm pass-through contains zero tracks and zero vias;
- the new edge geometry is topologically closed;
- routed copper, vias, and J4 pads meet the board-edge clearance checks used for this task;
- J4 has no local different-net copper clearance conflict;
- PMW routing remains deferred to Task 3E.

Final PCB Git blob:

```text
4272f9c3895fd46c0688b3eb530fc7299b540727
```

## Next

**Task 3E — route the PMW3360 interface from U1 to J4, plus VCC/GND, while MOTION remains NC.**
