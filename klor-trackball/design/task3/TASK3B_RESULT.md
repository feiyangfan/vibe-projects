# Task 3B result — schematic contract

Status: **COMPLETE**.

Task 3B implements the frozen Task 2 electrical interface in the **derivative schematic only**.

The derivative PCB intentionally remains byte-identical to the stock KLOR 1.4 board. Physical footprint deletion, connector synchronization, copper removal, and routing begin in Task 3C.

## Scope

Modified:

```text
PCB/konrad_trackball/konrad_trackball.kicad_sch
```

Not modified:

```text
PCB/konrad_trackball/konrad_trackball.kicad_pcb
klor1.4/PCB/klor1_4/*
```

This preserves the schematic-driven workflow established in Task 3A.

## Removed R34 circuit

The derivative schematic no longer contains:

- `SW22`;
- `D22`;
- the deleted-key local matrix branches.

The retained `col1` and `row3` nets remain present and separate.

No PCB footprint/copper removal occurs until 3C.

## RGB bypass

The old schematic path through SW22's SK6812 unit is removed.

The derivative schematic now connects:

```text
SW13 DOUT → SW14 DIN
```

directly.

This is the logical counterpart of the permanent copper bypass that Task 3C must implement on the PCB.

## MCU net ownership

Only the MCU-side stock ownership labels were replaced:

| MCU GPIO | Stock schematic label | Derivative label |
| --- | --- | --- |
| GP2 | `SDA` | `PMW_SCK` |
| GP3 | `SCL` | `PMW_MOSI` |
| GP4 | `RX` | `PMW_MISO` |
| GP9 | `AUDIO` | `PMW_CS` |

The old optional `SDA`, `SCL`, and `AUDIO` networks remain as isolated legacy circuitry where appropriate; they no longer own the MCU pins.

The `RX` global net is retired from the derivative schematic because J1.3 is no longer connected.

## PMW3360 connector

New schematic connector:

```text
Reference: J4
Value: PMW3360 Kivipallur
Symbol: Connector_Generic:Conn_01x07
Footprint: Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical
```

Pin contract:

| J4 pin | Net / state |
| ---: | --- |
| 1 | `PMW_CS` |
| 2 | `PMW_MISO` |
| 3 | `PMW_MOSI` |
| 4 | `PMW_SCK` |
| 5 | **NC** — mates to Kivipallur MOTION |
| 6 | `VCC` — mates to Kivipallur +3V3 |
| 7 | `GND` |

This is the Task 2C/2F **keyboard-side** order. It is deliberately reversed from the Kivipallur breakout's own numbering.

The connector exists only in the schematic during 3B. Task 3C will synchronize it onto the PCB; Task 3D owns its final physical XY/rotation and pass-through geometry.

## TRRS / split contract

J1.3 is now explicitly **no-connect** in the schematic.

The old J1.3 `RX` wire and label are removed.

The active split transport remains unchanged:

```text
GP1 → TX → J1.4
mode: half-duplex
```

Physical removal of the verified GP4-to-J1.3 PCB copper occurs in Task 3C.

## Revision-1 optional hardware state

The schematic now marks these stock optional loads as DNP:

- `J2` — haptic module;
- `OLED1` — OLED;
- `BZ1` — buzzer/audio.

Their legacy nets may remain in the schematic as isolated/open reference circuitry, but they no longer own GP2/GP3/GP9.

This mirrors the Task 2 firmware contract in which OLED, haptic, audio/music, PAW3204, I2C1, and audio PWM ownership are disabled for revision 1.

## What 3B deliberately does not do

Task 3B does not:

- update footprints from schematic;
- remove SW22/D22 from the PCB;
- add J4 to the PCB;
- remove the physical J1.3 RX segment;
- modify the RGB PCB copper;
- place the trackball connector;
- create the fabricated breakout pass-through;
- route PMW3360 signals;
- change board edges.

Those operations belong to Tasks 3C–3E.

## Verification

The Task 3B audit verifies:

- stock schematic and PCB Git objects remain locked;
- derivative PCB is still byte-identical to stock;
- SW22/D22 are absent from the derivative schematic;
- `col1` and `row3` remain present;
- the four MCU-side PMW labels are exact;
- each PMW signal appears exactly once at U1 and once at J4;
- J4 is a 1×7 / 2.54 mm through-hole connector with the frozen pin contract;
- J4 pin 5 / MOTION is explicitly NC;
- J1.3 is explicitly NC;
- J1.4/TX remains connected;
- SW13 DOUT → SW14 DIN exists directly;
- all obsolete SW22/J1.3 branch UUIDs are absent;
- J2, OLED1, and BZ1 are marked DNP;
- J4 is not yet present on the PCB, proving 3C work has not been mixed into 3B.

The audit also checks balanced KiCad s-expression structure. Full board/schematic DRC/ERC consolidation remains part of Task 3F after schematic-to-PCB synchronization.

**Task 3B: COMPLETE.**

Next: **Task 3C — apply the destructive stock-PCB edits and synchronize the schematic contract onto the board.**

## Post-completion representation normalization

The PCB baseline was later normalized for repository-tool access by removing only KiCad's regenerable cached `filled_polygon` data. This does not reopen the completed electrical/mechanical decisions. The normalized stock/derivative PCB blob is `3dea93bc4266541e9ca85eebc70e4b8c851afc11`; subsequent Task 3 work uses that representation.
