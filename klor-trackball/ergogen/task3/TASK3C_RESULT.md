# Task 3C Result — Left Production-Intent PCB

## Status

**PASS — Task 3C is complete.**

Task 3C generates the electrically complete, intentionally unrouted left Rev-1 PCB from the frozen Task-2 geometry, Task-3A electrical architecture, and Task-3B qualified local footprints.

## Qualified implementation

Generated PCB:

`task3c_left_production.kicad_pcb`

Production content:

- 20 MX hotswap + SK6812MINI-E sites;
- 21 COL2ROW matrix diodes;
- 20 RGB devices;
- one EC11 encoder with rotary A/B and diode-isolated push;
- one 0xCB Helios rev1.0 controller at the frozen U1 position;
- one MJ-4PP-9 TRRS split connector;
- one reset switch;
- eight M3 and one M2 frozen PCB mounting holes;
- no PMW3360 connector or PMW nets on the left half;
- no tracks, vias, or copper zones.

Routing remains owned by Task 4.

## Matrix-diode correction

The earlier Task-3 roadmap listed 20 left matrix diodes. That was inconsistent with the already-frozen 21-position matrix.

The checked-in stock PCB proves the encoder push path is:

```text
SW18.S2 -> D18 -> ROW3
```

Therefore the correct left production count is:

- 20 MX keys;
- 20 MX-key diodes;
- 1 encoder-click diode D18;
- **21 matrix diodes total**.

For the same reason, Task 3D is expected to use 20 diodes for 19 MX keys plus the right encoder click.

## Electrical result

The generated left board validates:

- 20 MX positions plus encoder click = 21 unique COL2ROW matrix positions;
- the frozen 20-device RGB chain;
- Helios left-side GPIO ownership exactly as frozen in Task 3A;
- GP2 / GP3 / GP4 / GP9 remain unused on the left;
- no right-only PMW SPI nets appear;
- TRRS = RAW_5V / GND / NC / SPLIT_DATA;
- reset shorts RESET to GND;
- all production SMD devices use the Task-3B qualified one-sided footprint variants;
- all nine PCB mounting axes remain frozen.

## Geometry

The board uses the unchanged Task-2 `stock_board` outline.

Production footprint placement is expressed in the canonical Task-2 frame. The validator explicitly verifies the canonical-to-KiCad reflection:

```text
canonical (x, y, rotation)
       -> KiCad (x, -y, -rotation)
```

No retained key, encoder, MCU, TRRS, or mounting axis was moved.

## Validation

Qualification head:

`fbc24e56e85c680d0260a86fa3d16109b7b685f8`

Passing workflow:

- workflow: `KLOR Task 3C - left production PCB`
- run ID: `35842345251`
- conclusion: **success**

The same head also passed the Task 2B, 2C, 2D, 3A, and 3B workflows.

The Task-3C workflow proves:

1. two clean Ergogen 4.2.1 generations are byte-for-byte deterministic;
2. all upstream geometry/electrical/footprint gates still pass;
3. exact left production footprint counts and placements;
4. the 21-position matrix topology;
5. the exact 20-device RGB chain;
6. left Helios GPIO ownership and absence of PMW nets;
7. coherent split, reset, power, and mounting interfaces;
8. absence of tracks, vias, and copper zones.

Qualification artifact:

- name: `klor-task3c-left-production-pcb`
- artifact ID: `10741886618`
- SHA-256: `b9012a6c63484b4bed2e9bddea10eeb33158d63e0ed5099cbc51088dabc2cb0b`

## Next

Proceed to **Task 3D — generate the right production-intent PCB with the frozen PMW3360 interface**.
