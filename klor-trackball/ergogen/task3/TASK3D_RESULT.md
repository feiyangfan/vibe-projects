# Task 3D Result — Right Production-Intent PCB

## Status

**PASS — Task 3D is complete.**

Task 3D generates the electrically complete, intentionally unrouted right Rev-1 PCB from the frozen Task-2D trackball geometry, Task-3A electrical architecture, Task-3B qualified local footprints, and the completed Task-3C left-board baseline.

## Qualified implementation

Generated PCB:

`task3d_right_production.kicad_pcb`

Production content:

- 19 MX hotswap + SK6812MINI-E sites;
- 20 COL2ROW matrix diodes;
- 19 RGB devices;
- one EC11 encoder with diode-isolated push;
- one 0xCB Helios rev1.0 controller at the frozen U1 position;
- one MJ-4PP-9 TRRS split connector;
- one reset switch;
- one frozen PMW 1x7 connector;
- eight M3 and one M2 frozen PCB mounting holes;
- no tracks, vias, or copper zones.

Routing remains owned by Task 4.

## Removed R34 site

The right board retains:

- SW20 / R32;
- SW21 / R33.

It omits:

- SW22 / R34;
- D22;
- the SW22 RGB device.

The right RGB chain therefore contains 19 devices and directly bypasses the removed SW22 site.

## Right production side

Rev 1 uses separate non-reversible production PCBs.

Task 3C uses the qualified B-side SMD variants on the left half. Task 3D uses the opposite qualified F-side variants for right-side keys, diodes, TRRS and reset.

The PMW header remains on F.Cu as frozen in Task 2D.

## Matrix and encoder

The generated right board validates:

- 19 MX positions;
- one encoder-click matrix position;
- 20 unique COL2ROW matrix positions total;
- D18 remains the encoder-click diode;
- right rotary direction semantics are preserved:
  - EC11 A -> GP29 / Helios pad 26;
  - EC11 B -> GP28 / Helios pad 25.

## PMW3360 interface

The generated board preserves the frozen Task-2D PMW header center and Y-axis row.

Physical pin order from negative canonical Y to positive canonical Y:

1. PMW_CS
2. PMW_MISO
3. PMW_MOSI
4. PMW_SCK
5. NC_MOTION
6. V3V3
7. GND

Controller ownership:

- GP2 / Helios pad 6 -> PMW_SCK;
- GP3 / Helios pad 7 -> PMW_MOSI;
- GP4 / Helios pad 8 -> PMW_MISO;
- GP9 / Helios pad 13 -> PMW_CS;
- Helios pad 27 -> V3V3;
- MOTION remains electrically NC and firmware uses polling.

The production PMW instance is rotated 180 degrees in the canonical frame so the qualified footprint's local pin order maps to the frozen physical negative-Y-to-positive-Y order after canonical-to-KiCad reflection.

## Geometry

The right PCB uses exactly the frozen Task-2D composition:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

No retained key, encoder, MCU, TRRS, mounting axis, ball/housing datum, breakout datum, PMW center, service corridor, or support-tongue geometry is moved.

## Validation

Qualification head:

`3da79cf1a8741409f27643b90acc02ef7142cfe1`

Passing workflow:

- workflow: `KLOR Task 3D - right production PCB`
- run ID: `35940504521`
- conclusion: **success**

The same head also passed:

- Task 2B;
- Task 2C;
- Task 2D;
- Task 3A;
- Task 3B;
- Task 3C.

The Task-3D workflow proves:

1. two clean Ergogen 4.2.1 generations are deterministic;
2. all upstream geometry/electrical/footprint/left-board gates still pass;
3. exact right production footprint counts and F-side SMD population;
4. the 20-position right matrix;
5. the exact 19-device RGB chain with SW22 bypassed;
6. the right encoder GP28/GP29 ownership swap;
7. frozen PMW center, orientation, physical pin order, SPI ownership, and 3V3 ownership;
8. absence of SW22/D22/R34 electrical leakage;
9. absence of tracks, vias, and copper zones.

Qualification artifact:

- name: `klor-task3d-right-production-pcb`
- artifact ID: `10784173764`
- SHA-256: `db58d1118cc6fc76143cda23da3ab4c666c69b163f4832c3e31e74685eba8944`

## Next

Proceed to **Task 3E — cross-board electrical integration and freeze**.
