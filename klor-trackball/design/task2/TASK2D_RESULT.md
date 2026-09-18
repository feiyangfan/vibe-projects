# Task 2D result — PCB net contract

Status: **complete**.

Task 2D composes the source-backed Task 2B GPIO ownership with the Task 2C physical connector contract and freezes the exact PCB net contract that the right-hand trackball derivative must implement in Task 3.

No production KLOR PCB geometry or firmware is modified by this task.

## Sources

- `design/task2/TASK2B_RESULT.md`
- `design/task2/TASK2C_RESULT.md`
- fresh JSON evidence from `audit_task2b_gpio_trrs.py`
- fresh JSON evidence from `audit_task2c_kivipallur_connector.py`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_sch`
- `design/task2/audit_task2d_pcb_net_contract.py`
- `.github/workflows/klor-task2d-pcb-net-contract-audit.yml`

The Task 2D CI workflow rebuilds the 2B and 2C evidence from source on every run before evaluating this contract.

## Locked connector-to-net contract

Task 2C fixes the KLOR keyboard-side physical order as:

```text
pin 1  CS
pin 2  MISO
pin 3  MOSI
pin 4  SCK
pin 5  NC / breakout MOTION
pin 6  3V3
pin 7  GND
```

Task 2D attaches each physical pin to one target PCB net and, where applicable, one MCU GPIO:

| KLOR pin | Breakout signal | Target KLOR derivative net | MCU / U1 pad | Stock source net | Required stock disposition |
| ---: | --- | --- | --- | --- | --- |
| 1 | CS | `PMW_CS` | GP9 / U1.12 | `AUDIO` | disable audio; BZ1 DNP/no active load |
| 2 | MISO | `PMW_MISO` | GP4 / U1.7 | `RX` | isolate TRRS J1.3 using the Task 2B-verified F.Cu branch |
| 3 | MOSI | `PMW_MOSI` | GP3 / U1.6 | `SCL` | disable I2C/PAW3204; J2 haptic DNP; legacy I2C jumpers open |
| 4 | SCK | `PMW_SCK` | GP2 / U1.5 | `SDA` | disable I2C/PAW3204; legacy I2C jumpers open |
| 5 | MOTION | **NC** | none | none | connector pad remains unrouted/unassigned for revision 1 |
| 6 | +3V3 | `VCC` | U1.21 / VCC rail | `VCC` | direct connection to existing KLOR controller VCC rail |
| 7 | GND | `GND` | U1.3/U1.4/U1.23 ground rail | `GND` | direct connection to existing ground |

## Important power-rail correction

The prior planning shorthand called the KLOR-side power net `3V3`. The actual stock KLOR source does **not** define a PCB/schematic net named `3V3`; it uses `VCC`.

The selected controller is the Elite-Pi. In this RP2040/Pro-Micro-compatible configuration, the controller VCC rail is the 3.3 V rail. Therefore the implementation contract is:

```text
Kivipallur +3V3 -> KLOR VCC
Kivipallur GND  -> KLOR GND
```

Task 3 must use the existing KLOR `VCC` and `GND` rails. It must not create a second `3V3` power net merely to match the breakout's net label.

The source audit additionally locks:

- U1 pad 21 = `VCC`, stock net id 3;
- U1 pads 3, 4, and 23 = `GND`, stock net id 1.

## Target net naming

For the four SPI signals, the derivative uses explicit trackball-semantic net names:

```text
PMW_CS
PMW_MISO
PMW_MOSI
PMW_SCK
```

The stock names `AUDIO`, `RX`, `SCL`, and `SDA` are **source-topology names**, not acceptable final semantic names for the reassigned PMW signal nets.

This matters because retaining the old names would obscure ownership and make it easier to accidentally preserve a conflicting legacy load. Task 3 should rename/recreate the affected signal nets as the `PMW_*` nets above while implementing the already-locked isolation/open/DNP rules from Task 2B.

## Pin-by-pin implementation rules

### Pin 1 — CS / GP9

Target:

```text
KLOR connector pin 1 -> PMW_CS -> U1.12 / GP9
```

Stock source is `AUDIO`. QMK audio is disabled for the trackball variant and BZ1 must not be an active load. Obsolete audio copper/footprint may be removed where useful.

### Pin 2 — MISO / GP4

Target:

```text
KLOR connector pin 2 -> PMW_MISO -> U1.7 / GP4
```

Stock source is `RX`. The Task 2B-verified J1.3-adjacent branch must be removed so TRRS J1.3 becomes NC while GP1/J1.4 remains intact for half-duplex split serial.

### Pin 3 — MOSI / GP3

Target:

```text
KLOR connector pin 3 -> PMW_MOSI -> U1.6 / GP3
```

Stock source is `SCL`. I2C and PAW3204 ownership are retired on the trackball right half. J2 haptic remains DNP and the legacy reversible/I2C jumpers remain open.

### Pin 4 — SCK / GP2

Target:

```text
KLOR connector pin 4 -> PMW_SCK -> U1.5 / GP2
```

Stock source is `SDA`. I2C and PAW3204 ownership are retired and legacy reversible/I2C jumpers remain open.

### Pin 5 — MOTION / NC

Revision 1 does not use the Kivipallur MOTION output.

Target:

```text
KLOR connector pin 5 -> electrically unconnected
```

The connector pad exists physically, but Task 3 must not route it to an MCU pin, test pad, or another net unless Task 2 is explicitly reopened.

### Pin 6 — +3V3 / VCC

Target:

```text
KLOR connector pin 6 -> VCC
```

This is the existing KLOR controller VCC rail and is the 3.3 V supply for the selected Elite-Pi configuration.

### Pin 7 — GND

Target:

```text
KLOR connector pin 7 -> GND
```

Use the existing KLOR ground rail/plane.

## What Task 3 is and is not allowed to change

Task 3 owns physical routing, final connector XY placement within the Task 2C orientation constraint, and the real breakout pass-through/edge clearance.

Task 3 may:

- prune obsolete AUDIO/I2C/haptic/PAW branch copper or unused footprints when useful;
- choose trace layers, widths, vias, and routing paths consistent with DRC;
- connect the PMW power pins into the existing VCC/GND distribution.

Task 3 may **not**:

- reorder connector pins;
- copy Kivipallur breakout numbering directly onto the keyboard side;
- assign MOTION to an MCU pin;
- reconnect J1.3 to GP4;
- leave an active audio load on GP9;
- leave active I2C/PAW3204 ownership on GP2/GP3;
- create a separate KLOR `3V3` rail instead of using the existing `VCC` rail;
- rename the four final SPI nets back to their legacy functional names.

## Completion gate

Task 2D passes when fresh 2B and 2C audits pass and the composed contract verifies:

- all seven physical connector pins are accounted for;
- CS -> `PMW_CS` -> GP9 / U1.12;
- MISO -> `PMW_MISO` -> GP4 / U1.7;
- MOSI -> `PMW_MOSI` -> GP3 / U1.6;
- SCK -> `PMW_SCK` -> GP2 / U1.5;
- MOTION is NC;
- breakout +3V3 maps to stock KLOR `VCC`;
- GND maps to stock KLOR `GND`;
- the four PMW signal nets are unique;
- no connector pin has unresolved MCU/net ownership.

**Task 2D: COMPLETE.**

Next dependency: **Task 2E — freeze firmware ownership.**
