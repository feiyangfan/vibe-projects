# Task 3 — Production Electrical PCB

Task 3 converts the frozen Task-2 geometry into a production-intent **unrouted** electrical PCB definition.

Routing is deliberately excluded. Task 4 owns routing and regeneration safety.

## Dependency

Task 3 consumes the frozen Task-2 contract:

`../task2/task2d-freeze.yaml`

Task 3 may add electrical implementation detail, but it may not silently move or reinterpret Task-2 geometry.

## Subtasks

### Task 3A — Freeze the electrical architecture

**COMPLETE**

Freeze:

- exact RP2040 Pro-Micro-class controller;
- power domains;
- matrix row/column ownership;
- diode direction;
- split transport;
- RGB power/data ownership and chain order;
- both rotary encoders and encoder-click matrix positions;
- PMW3360 SPI and 1x7 electrical contract;
- reset behavior;
- explicit removal of obsolete stock peripherals;
- GPIO ownership and unused-pin policy.

Gate:

- one machine-readable electrical contract exists;
- every required signal has exactly one controller owner per half;
- there are no GPIO conflicts;
- left/right matrix occupancy and RGB counts match the frozen product;
- PMW connector power/signal mapping matches the frozen Task-2 mechanical contract;
- removed Rev-1 features own no GPIO or electrical interface.

### Task 3B — Qualify production footprints

**COMPLETE**

Validate or implement local production footprints for:

- MX hotswap + SK6812 Mini-E;
- 1N4148W / SOD-123;
- selected RP2040 controller;
- TRRS;
- EC11 encoder;
- reset switch;
- PMW 1x7 connector;
- PCB mounting hardware.

Gate:

- every Rev-1 electrical component has a deterministic local footprint;
- pad numbering, orientation, layers, drills, paste/mask and physical envelope are source-audited;
- the selected controller footprint fits the frozen U1 envelope and exposes every Task-3A-required pad.

### Task 3C — Generate the left production-intent PCB

**COMPLETE**

Generate the electrically complete, unrouted left PCB from source.

Expected electrical content:

- 20 MX keys;
- 21 matrix diodes (20 MX + encoder click D18);
- 20 RGB devices;
- encoder rotary A/B plus encoder push;
- controller;
- TRRS half-duplex split;
- reset;
- power/ground.

Gate:

- the left PCB regenerates deterministically;
- every required footprint/net exists exactly once;
- the local matrix has 21 active switch positions: 20 MX + encoder push;
- the board is electrically coherent and intentionally unrouted.

### Task 3D — Generate the right production-intent PCB

**REVISION 6 — COMPLETE**

Generate the right PCB on the frozen Task-2 revision-6 mesh-verified trackball geometry.

Expected electrical content:

- 19 MX keys;
- 20 matrix diodes (19 MX + encoder click D18);
- 19 RGB devices;
- right encoder rotary A/B plus encoder push;
- controller;
- TRRS half-duplex split;
- reset;
- cabled PMW 1x7 board header on F.Cu; the Kivipallur breakout remains on the right side of the ball;
- PMW3360 SPI/power nets.

Gate:

- R32/R33 remain;
- R34/SW22/D22 and its RGB device are absent;
- the RGB chain bypasses R34 logically;
- the Kivipallur breakout remains on the right/+X side of the ball;
- the board-side PMW header remains at the frozen Rev-6 cable-header datum `(0, -22.022143)`, with its row on canonical Y;
- the generated PCB uses the frozen actual-housing-derived cavity;
- Task 2E proves zero meaningful housing/sphere intersection with the generated PCB;
- the right PCB is electrically coherent and intentionally unrouted.

### Task 3E — Cross-board electrical integration and freeze

**COMPLETE**

Validate the left and right generated boards as one split keyboard.

Gate:

- 20/19 MX and RGB counts are exact;
- both encoder clicks are represented in the matrix;
- split power/data contracts match;
- matrix/diode direction is coherent;
- GPIO ownership is conflict-free;
- right-only PMW ownership is exact;
- removed stock features do not reappear;
- Task-2 geometry remains unchanged;
- the pair is ready for Task 4 routing.

Qualification:

- workflow: `KLOR Task 3E - cross-board electrical freeze`;
- first passing run: `37722057338`;
- qualification head: `f1b8d065d64a5725c15c6181061fc0c142549896`;
- artifact: `klor-task3e-unrouted-pcb-pair` / ID `11525704458`;
- artifact SHA-256: `df5cf72b325dfbd58a987fa5ab20d28a60d6d84fd2bb2c13da030303055bb4d5`.

The Task-3E gate regenerated the pair twice, proved byte-for-byte deterministic output, reran Tasks 2B/2C/2D and 3A/3B/3C/3D, and then passed the pair-level electrical freeze.

## Task-3 completion definition

**Status: COMPLETE.** Task 3 completes when a clean checkout deterministically generates two electrically coherent **unrouted production-intent KiCad PCBs** from source and the pair-level electrical contract passes regression.

The completion gate is satisfied. A routed board is explicitly **not** required until Task 4. The revision-6 physical right-half mock-up should pass before Task 4 routing is treated as production-final.
