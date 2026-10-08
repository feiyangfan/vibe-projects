# Task 4 — Regeneration-Safe Routing

Task 4 converts the frozen Task-3 unrouted PCB pair into routed production-intent boards without reintroducing manual, identity-dependent KiCad surgery.

## Dependency

Task 4 consumes:

- Task-2 Revision-6 geometry;
- the Task-3E pair-level electrical freeze;
- generated left and right production-intent KiCad PCBs.

Routing may not silently move footprints, alter the matrix/RGB/split/PMW contracts, or reinterpret the Rev-6 trackball geometry.

## Subtasks

### Task 4A — Freeze routing rules and net classes

**IN PROGRESS**

Define the manufacturing/routing contract before adding copper.

Freeze:

- layer/stack-up assumptions;
- default signal width and clearance;
- power width;
- standard and power via geometry;
- board-edge and hole clearances;
- ground-zone policy;
- net-class ownership;
- per-half layer preferences;
- PMW/SPI routing constraints;
- routing-style rules that Task 4B–4F must obey.

Gate:

- one machine-readable routing contract exists;
- every frozen Task-3 signal family maps to one routing class;
- rules are compatible with the stock KLOR fabrication reference and selected Rev-1 fabrication envelope;
- no routed copper is added yet.

### Task 4B — Prove the regeneration-safe routing mechanism

Build the smallest useful routed slice before bulk routing.

Requirements:

- select representative nets from at least matrix plus one non-matrix class;
- route them using net names and canonical/generated geometry rather than KiCad UUID/object identity;
- regenerate from a clean source tree;
- make one controlled upstream placement/geometry perturbation in a test fixture;
- prove the routing can be regenerated/replayed without manually editing tracks.

Gate:

- the routing mechanism is deterministic/replayable;
- the proof does not depend on exact generated object IDs;
- the method is suitable for scaling to the whole keyboard.

### Task 4C — Route the left PCB

Route the complete left half using the proven 4B mechanism:

- matrix;
- encoder and reset;
- split transport;
- RGB;
- RAW_5V / V3V3 as applicable;
- ground strategy.

Gate:

- zero unrouted required nets;
- routing obeys the 4A contract;
- generated/replayed result is deterministic;
- DRC passes for the left board.

### Task 4D — Route the right PCB excluding PMW

Route the ordinary keyboard circuitry on the Rev-6 right half:

- matrix;
- encoder and reset;
- split transport;
- RGB;
- ordinary power/ground distribution.

Do not route the PMW3360 interface in this subtask.

Gate:

- ordinary right-half nets are complete;
- PMW nets remain intentionally unrouted;
- Rev-6 cavity/housing/header geometry and keepouts remain unchanged;
- DRC passes apart from the intentionally deferred PMW connections.

### Task 4E — Route the PMW3360 interface

Route the right-only interface:

- PMW_SCK;
- PMW_MOSI;
- PMW_MISO;
- PMW_CS;
- V3V3;
- GND to the 1x7 board header.

Gate:

- PMW routing obeys the 4A SPI/power rules;
- PMW ownership remains right-only;
- the frozen 1x7 pin order and cable mapping remain unchanged;
- Rev-6 mechanical regression still passes;
- the right board has zero required unrouted nets.

### Task 4F — Pair-level DRC, regeneration test, and routing freeze

Validate both routed boards as the final Task-4 pair.

Gate:

- clean checkout regenerates both routed boards deterministically;
- KiCad DRC passes on both boards;
- no required unrouted nets remain;
- power/ground continuity and zone strategy pass regression;
- Tasks 2B/2C/2D/2E and 3A/3B/3C/3D/3E still pass;
- repeat the required upstream-change regeneration test;
- freeze the routed pair for Task 5+.

## Task-4 completion definition

Task 4 is complete only when routing is reproducible from source, not merely when one KiCad file happens to be routed.

A physical Revision-6 right-half mock-up remains required before the Task-4 routed result is treated as production-final.
