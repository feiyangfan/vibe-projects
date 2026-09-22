# Task 3 — Right-Hand Trackball PCB Derivative

Status: **IN PROGRESS**

Task 3 converts the locked Task 1 mechanical placement and locked Task 2 electrical/firmware interface into an editable, schematic-driven KiCad PCB derivative for the right half of KLOR 1.4 MX Konrad.

Task 3 does not redesign the electrical architecture. It implements the already-frozen Task 2 contract while preserving unrelated stock circuitry and the Task 1 mechanical constraints.

## Dependency chain

```text
3A → 3B → 3C → 3D → 3E → 3F → 3G
```

Each subtask has a separate gate so electrical logic, destructive edits, mechanical PCB integration, routing, and final validation do not get mixed into one opaque PCB change.

---

## Locked inputs

Task 3 consumes, without changing:

- Task 1 mechanical reference placement: [`../task1/README.md`](../task1/README.md)
- Task 2 electrical/firmware interface: [`../task2/README.md`](../task2/README.md)
- final Task 2 interface freeze: [`../task2/TASK2F_RESULT.md`](../task2/TASK2F_RESULT.md)
- canonical geometry/electrical state: [`../konrad_trackball_geometry.yaml`](../konrad_trackball_geometry.yaml)

Stock KLOR source remains reference-only:

`../../klor1.4/PCB/klor1_4/`

The editable Task 3 derivative lives at:

`../../PCB/konrad_trackball/`

---

## 3A — Create the trackball KiCad derivative — COMPLETE

Create a distinct, schematic-driven KiCad project before any electrical edits.

The derivative must include:

- project file;
- schematic;
- PCB;
- design rules;
- local KLOR symbol library;
- local KLOR footprint library;
- footprint/symbol library tables;
- round-track configuration.

Task 3A intentionally excludes stock Gerbers/fabrication output.

Baseline invariants:

- stock KLOR source is not edited;
- derivative PCB starts byte-identical to stock;
- derivative schematic starts byte-identical to stock;
- design rules and local libraries start byte-identical to stock;
- the only intentional project-file content change is the KiCad project metadata filename;
- no Task 2 electrical changes are implemented yet.

**Gate:** [`TASK3A_RESULT.md`](TASK3A_RESULT.md) and the Task 3A audit pass.

---

## 3B — Implement the schematic contract — COMPLETE

Make the Task 2 electrical contract explicit in the derivative schematic before changing PCB routing.

Required logical changes include:

- remove `SW22`;
- remove `D22`;
- remove the obsolete R34 matrix branch;
- preserve `col1` and `row3` as separate nets;
- add the 1×7 keyboard-side PMW3360/Kivipallur connector;
- assign:
  - pin 1 → `PMW_CS` → GP9;
  - pin 2 → `PMW_MISO` → GP4;
  - pin 3 → `PMW_MOSI` → GP3;
  - pin 4 → `PMW_SCK` → GP2;
  - pin 5 → NC / MOTION unused;
  - pin 6 → `VCC`;
  - pin 7 → `GND`;
- make TRRS `J1.3` electrically unused;
- preserve GP1 / `J1.4` half-duplex split serial;
- retire the right-side schematic ownership that conflicts with GP2/GP3/GP9;
- represent haptic/audio/legacy optional paths consistently with the Task 2 DNP/disabled contract.

The connector reference selected in 3B is **J4**. Its physical pin order is the frozen keyboard-side order from Task 2:

```text
J4.1 PMW_CS
J4.2 PMW_MISO
J4.3 PMW_MOSI
J4.4 PMW_SCK
J4.5 NC / MOTION
J4.6 VCC
J4.7 GND
```

Task 3B also:

- removes SW22 and D22 from the derivative schematic;
- replaces the SW22 LED path with a direct `SW13 DOUT → SW14 DIN` schematic connection;
- changes the U1-side semantic ownership to `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- makes J1.3 explicitly NC while preserving J1.4/TX;
- marks J2, OLED1, and BZ1 DNP for revision 1;
- intentionally leaves the derivative PCB byte-identical to stock so physical synchronization is isolated to 3C.

The retired 3A workflow is no longer an active CI gate because its purpose was to prove a byte-identical starting baseline. Its audit script and result remain as historical evidence. Task 3B is now the active Task 3 regression gate.

**Gate:** [`TASK3B_RESULT.md`](TASK3B_RESULT.md) and the Task 3B structural contract audit pass. Full integrated ERC/DRC validation remains Task 3F after schematic-to-PCB synchronization.

---

## 3C — Apply destructive stock-PCB edits — COMPLETE

Task 3C synchronized the Task 3B contract onto the derivative PCB.

Implemented:

- removed `SW22` and `D22`;
- removed the complete local `Net-(D22-A)` circuit;
- removed only the `col1` and `row3` branches that served the deleted key;
- preserved the retained matrix trunks as distinct nets;
- retired PCB net `RX` and made J1.3 physically no-net;
- preserved GP1 / `TX` / J1.4;
- reassigned the physical U1 pads to `PMW_SCK`, `PMW_MOSI`, `PMW_MISO`, and `PMW_CS`;
- merged SW14 DIN into the retained SW13 DOUT net and added a permanent B.Cu bypass splice;
- introduced J4 with the frozen 1×7 electrical contract.

J4 is deliberately staged off-board at KiCad `(60, 70)` on `F.Cu`. This is **not** its production placement. Task 3D owns final connector XY/rotation and the fabricated breakout clearance.

No Edge.Cuts were changed in 3C. PMW signal routing from U1 to J4 is also deliberately deferred to 3E.

The Task 3C preservation audit proves exact authorized trace/via deletions, unchanged retained footprint placement, unchanged retained trace/via geometry, exact stock Edge.Cuts, correct J1/RGB/matrix state, and the frozen J4 pin contract.

**Gate:** [`TASK3C_RESULT.md`](TASK3C_RESULT.md) and the Task 3C PCB synchronization audit pass.

---

## 3D — Place connector and create fabricated breakout pass-through — COMPLETE

Implement the mechanical PCB interface using the locked Task 1/2 frame.

Locked orientation:

- breakout/pass-through datum: `(143.111, -134.748)` in KLOR Gerber/Excellon coordinates;
- connector side: `F.Cu`;
- row axis: global Y;
- pin 1: negative-Y end;
- pin 7: positive-Y end;
- connector on positive-X / non-sensor side;
- breakout insertion/service direction: negative X;
- keyboard-side row order:
  `CS, MISO, MOSI, SCK, NC, 3V3, GND`.

The Klorball35 2×22 mm rectangle is only a `Cmts.User` reference guide. 3D must create the actual manufacturable KLOR pass-through/edge clearance.

Final Task 3D geometry:

- locked slot center in KiCad: `(143.111043, 134.747997)`;
- actual pass-through: open 2 mm edge notch following the 2×22 mm service envelope;
- J4 pin-1/anchor: `(147.724665, 142.367997)`, rotation `0°`, `F.Cu`;
- J4 row midpoint: `(147.724665, 134.747997)`;
- header-row offset from the guide: `+4.613622 mm` X;
- local support tongue: right edge `X=150.0`, bottom edge `Y=144.25`;
- PMW signal routing remains deferred to 3E.

The pass-through intersects stock/3C VCC copper and the staged RGB bypass region. Task 3D therefore performs only the required local VCC/RGB reroutes to keep the fabricated opening copper-free.

**Gate:** [`TASK3D_RESULT.md`](TASK3D_RESULT.md) and the Task 3D connector/pass-through audit pass.

---

## 3E — Route the PMW3360 interface — COMPLETE

Route the frozen interface only after connector and pass-through geometry are fixed.

Required nets:

```text
PMW_CS   → GP9
PMW_MISO → GP4
PMW_MOSI → GP3
PMW_SCK  → GP2
VCC      → breakout +3V3
GND      → breakout GND
MOTION   → no route
```

3E owns trace layers, widths, vias, route shape, and local copper cleanup.

Required invariants:

- no PMW signal remains semantically named `AUDIO`, `RX`, `SCL`, or `SDA`;
- MOTION has no routed copper/net owner;
- every required PMW signal is fully routed;
- existing split/RGB/matrix/encoder ownership remains intact.

Implemented routing:

- `PMW_CS` → J4.1;
- `PMW_MISO` → J4.2;
- `PMW_MOSI` → J4.3;
- `PMW_SCK` → J4.4;
- J4.5 MOTION remains NC;
- J4.6 is tied to the existing `VCC` rail;
- J4.7 is tied to `GND`.

The routing is deterministic from the exact Task 3D PCB and is additive only. Existing Task 3D copper, geometry, footprints, zones, and schematic state are not rewritten.

**Gate:** [`TASK3E_RESULT.md`](TASK3E_RESULT.md) and the Task 3E routing/reproduction audit pass. Full KiCad DRC remains Task 3F.

---

## 3F — Preservation and DRC audit

Compare the derivative to the stock PCB and explicitly prove unrelated geometry/circuitry was not disturbed.

Protected items include:

- R32 and R33;
- right encoder;
- retained MX/SK6812 footprints;
- MCU placement;
- TRRS placement except the authorized J1.3 isolation;
- all structural mounting holes/axes;
- stock board geometry outside justified trackball edits;
- GP1 split path;
- unaffected matrix/RGB/power routing.

Validate:

- no dangling obsolete copper;
- no accidental net merges;
- no unexplained unrouted items;
- board-edge/pass-through clearances;
- KiCad DRC.

**Gate:** zero unexplained DRC failures and zero unauthorized stock changes.

---

## 3G — Freeze the Task 3 PCB derivative

Create one canonical Task 3 result containing:

- derivative project paths;
- exact connector reference, XY, rotation, side, and pin order;
- final fabricated pass-through/edge geometry;
- final PMW net/routing map;
- removed footprints and copper;
- RGB bypass;
- J1.3 isolation;
- retained-component preservation audit;
- DRC result;
- intentional exceptions, if any.

Update the project README, canonical geometry state, and engineering handoff together.

**Gate:**

```text
Task 3 COMPLETE
PCB derivative locked
Task 4 authorized
```

---

## Task 3 boundaries

Task 3 may choose:

- connector reference designator;
- exact connector XY within locked Task 2C orientation constraints;
- pass-through shape consistent with the locked service corridor;
- copper layers, trace widths, vias, and route geometry;
- local cleanup of obsolete circuitry explicitly retired by Task 2.

Task 3 may not change without reopening Task 1 or Task 2:

- trackball placement;
- connector pin order/handedness;
- PMW GPIO ownership;
- PMW semantic net names;
- `VCC` / `GND` mapping;
- MOTION = NC;
- GP1/`J1.4` split preservation;
- GP4/`J1.3` isolation requirement;
- SW22/D22 removal;
- RGB bypass topology;
- right optional-feature ownership.

---

## Fabrication boundary

Task 3 freezes the PCB design itself. Production Gerbers and independent manufacturing review remain Task 8 work.

Do not treat the board as fabrication-ready until downstream mechanical integration and firmware tasks also pass.

## PCB representation normalization

The stock PCB uses normalized blob `3dea93bc4266541e9ca85eebc70e4b8c851afc11`; the Task 3C derivative uses normalized blob `c3fefdb583d653a836d2ab99a9d94126ea331a3b` (~1.44 MB). Only KiCad's generated `filled_polygon` cache is omitted. Zone definitions and all physical/electrical PCB geometry remain committed.

Refill zones before DRC/fabrication and strip the cache again before committing.
