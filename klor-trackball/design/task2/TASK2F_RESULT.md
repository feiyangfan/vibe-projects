# Task 2F result — complete electrical/firmware interface freeze

Status: **complete**.

Task 2F is the final Task 2 completion gate. It rebuilds Tasks 2A through 2E from the checked-in sources, composes their results, and freezes one authoritative interface contract for the KLOR 1.4 MX Konrad right-hand PMW3360 derivative.

**Task 2 is complete. Task 3 PCB implementation is authorized against this contract.**

Task 2 does not modify the production PCB or production firmware; it defines exactly what Tasks 3 and 7 must implement.

## Canonical evidence

- `TASK2A_RESULT.md`
- `TASK2B_RESULT.md`
- `TASK2C_RESULT.md`
- `TASK2D_RESULT.md`
- `TASK2E_RESULT.md`
- `task2_manifest.yaml`
- `audit_task2f_interface_freeze.py`
- `.github/workflows/klor-task2f-interface-freeze.yml`

The Task 2F workflow regenerates every Task 2A–2E JSON audit artifact before running the final freeze. It therefore fails if any upstream source topology drifts away from the frozen contract.

---

## Final connector / net / GPIO / firmware contract

The KLOR-side connector is the Task 2C keyboard-side mate, not a copy of the Kivipallur breakout numbering.

| KLOR keyboard pin | Kivipallur breakout pin | Breakout signal | Final PCB net | MCU / U1 pad | Firmware function | Required stock-circuit change |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 7 | CS | `PMW_CS` | GP9 / U1.12 | PMW3360 CS | retire `AUDIO`; disable audio/music + PWM4; BZ1 DNP/no active load |
| 2 | 6 | MISO | `PMW_MISO` | GP4 / U1.7 | SPI0 MISO / PMW3360 MISO | remove verified `RX` branch to TRRS `J1.3`; J1.3 becomes NC; full duplex remains disabled |
| 3 | 5 | MOSI | `PMW_MOSI` | GP3 / U1.6 | SPI0 MOSI / PMW3360 MOSI | retire `SCL`/I2C1/PAW3204; J2 haptic DNP; legacy I2C jumpers open |
| 4 | 4 | SCK | `PMW_SCK` | GP2 / U1.5 | SPI0 SCK / PMW3360 SCK | retire `SDA`/I2C1/PAW3204; legacy I2C jumpers open |
| 5 | 3 | MOTION | **NC** | none | unused; sensor is polled | leave connector pad unrouted/unassigned; do not define a motion GPIO |
| 6 | 2 | +3V3 | `VCC` | U1.21 / VCC | 3.3 V supply | connect to existing KLOR `VCC`; do not create a separate KLOR `3V3` net |
| 7 | 1 | GND | `GND` | U1 ground rail | ground | connect to existing KLOR GND |

The opposite-facing mate is permanently:

```text
Kivipallur breakout pin N <-> KLOR keyboard pin (8-N)
```

Do not copy the breakout pin numbering directly onto the KLOR-side connector.

---

## Connector physical orientation

Locked from Task 2C against the Task 1 canonical fabrication frame:

- connector footprint: 1×7 vertical through-hole, 2.54 mm pitch;
- KLOR keyboard connector side: `F.Cu`;
- connector row axis: global Y;
- pin 1: negative-Y end;
- pin 7: positive-Y end;
- row order from negative Y to positive Y:
  `CS, MISO, MOSI, SCK, NC, 3V3, GND`;
- connector is on the positive-X / non-sensor side of the breakout guide;
- breakout service direction: negative X;
- Task 1 breakout/pass-through center: `(143.111, -134.748)` in KLOR Gerber/Excellon coordinates.

The Klorball35 2×22 mm rectangle is a `Cmts.User` reference guide, **not** a fabrication cut. Task 3 must create the actual KLOR pass-through/edge clearance while keeping the locked orientation and service direction.

---

## Required removed-key and RGB changes

Logical Konrad key R34 is PCB `SW22`, matrix position `[7,1]`.

Task 3 must:

1. remove `SW22`;
2. remove `D22`;
3. delete the obsolete local `Net-(D22-A)` copper;
4. preserve the `col1` and `row3` trunks;
5. **not bridge** `col1` and `row3`;
6. remove the integrated SW22 SK6812 from the RGB chain;
7. permanently bypass it in copper:

```text
SW13 DOUT -> SW14 DIN
```

Shared VCC/GND rail continuity must remain intact.

Final RGB ownership/topology:

```text
GPIO: GP0
left:  20 LEDs
right: 19 LEDs
total: 39 LEDs
```

Detailed QMK `g_led_config` remains a Task 7 implementation item.

---

## Split/TRRS contract

The active split transport remains unchanged:

```text
GP1 -> TX -> J1.4
mode: half-duplex
```

Preserve it.

GP4 is reassigned to PMW3360 MISO. The exact stock J1.3 branch that Task 3 must remove is:

```text
net: RX (28)
layer: F.Cu
width: 0.254 mm
from: (92.700, 127.025)
to:   (90.880, 127.025)
```

After the edit:

```text
J1.3 = NC
GP4 = PMW_MISO only
J1.4 / GP1 half-duplex split = preserved
```

Firmware-only disabling of full duplex is not sufficient; the copper isolation is mandatory.

---

## Optional stock peripheral contract

Revision 1 intentionally retires these right-side stock features:

| Feature | Hardware state | Firmware state |
| --- | --- | --- |
| OLED | DNP / legacy I2C jumpers remain open | disabled |
| haptic | J2 DNP; I2C paths inactive | disabled |
| audio | BZ1 inactive/DNP | disabled |
| music | n/a | disabled |
| stock PAW3204 | unused | disabled |
| I2C1 | no active right-side user | disabled |
| PWM4 audio | no active user | disabled |

GP2 and GP3 become SPI signals exclusively. GP9 becomes PMW CS exclusively.

---

## Final QMK ownership contract

### GPIO ownership

| GPIO | Revision-1 owner |
| --- | --- |
| GP0 | WS2812 / RGB matrix |
| GP1 | split serial, half duplex |
| GP2 | PMW3360 SCK |
| GP3 | PMW3360 MOSI |
| GP4 | PMW3360 MISO |
| GP5/6/7/8 | matrix rows |
| GP9 | PMW3360 CS |
| GP20/21/22/23/26/27 | matrix columns |
| GP28/29 | encoder |

There is **zero overlapping revision-1 GPIO ownership**.

### PMW3360 / SPI0

Task 7 must implement the equivalent of:

```text
POINTING_DEVICE_ENABLE = yes
POINTING_DEVICE_DRIVER = pmw3360
SPI_DRIVER_REQUIRED = yes

SPI_DRIVER = SPID0
SPI_SCK_PIN = GP2
SPI_MOSI_PIN = GP3
SPI_MISO_PIN = GP4
PMW33XX_CS_PIN = GP9

SPLIT_POINTING_ENABLE
POINTING_DEVICE_RIGHT
EE_HANDS
```

Revision 1 does not define `POINTING_DEVICE_MOTION_PIN`.

### ChibiOS peripheral ownership

Target state:

```text
HAL_USE_SPI        = TRUE
RP_SPI_USE_SPI0    = TRUE
RP_SPI_USE_SPI1    = FALSE

HAL_USE_I2C        = FALSE
RP_I2C_USE_I2C1   = FALSE

HAL_USE_PWM        = FALSE
RP_PWM_USE_PWM4    = FALSE
```

### Stock QMK declarations that must not survive in the trackball derivative

Remove/omit the conflicting ownership represented by:

- `I2C1_SDA_PIN GP2`
- `I2C1_SCL_PIN GP3`
- `PAW3204_SDIO_PIN GP2`
- `PAW3204_SCLK_PIN GP3`
- `AUDIO_PIN GP9`
- optional full-duplex `SERIAL_USART_TX_PIN GP4`
- optional `SERIAL_USART_RX_PIN GP1`
- `SERIAL_USART_FULL_DUPLEX`
- `SERIAL_USART_PIN_SWAP`
- `I2C_DRIVER_REQUIRED = yes`
- `AUDIO_DRIVER = pwm_hardware`

The stock default and Vial keymap `rules.mk` files both re-enable OLED/audio/haptic. Neither may be reused unchanged for the trackball firmware build.

---

## Retained matrix and encoder ownership

Rows remain:

```text
GP5 GP6 GP7 GP8
```

Columns remain:

```text
GP27 GP26 GP22 GP20 GP23 GP21
```

Only matrix position `[7,1]` / R34 is removed.

Encoder ownership remains:

```text
left:  A GP28 / B GP29
right: A GP29 / B GP28
```

---

## Deferred to Task 7 bring-up

The electrical ownership is frozen, but these behavioral parameters intentionally remain adjustable during firmware/hardware bring-up:

- pointer X/Y rotation;
- axis inversion;
- CPI/sensitivity;
- lift-off distance;
- scrolling behavior;
- acceleration;
- auto-mouse behavior.

The revision-1 baseline leaves auto-mouse disabled until raw PMW3360 motion is confirmed.

Changing these parameters does **not** reopen Task 2 unless the GPIO/net/connector interface itself changes.

---

## Task 3 authorization

Task 3 is now authorized to create the right-hand trackball PCB derivative.

Task 3 must implement this Task 2 contract exactly, including:

- SW22 + D22 deletion;
- no matrix-net bridge;
- `SW13 DOUT -> SW14 DIN` RGB bypass;
- final PMW connector orientation and pin order;
- `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, `PMW_SCK` nets;
- +3V3 breakout pin mapped to KLOR `VCC`;
- MOTION NC;
- exact J1.3/GP4 copper isolation;
- GP1/J1.4 split preservation;
- J2 haptic DNP and I2C jumpers open;
- BZ1 inactive/DNP;
- actual fabricated breakout pass-through/edge clearance.

Task 3 may choose routing layers, widths, vias, local obsolete-copper cleanup, and final connector XY consistent with the Task 2C orientation and Task 1 mechanical assembly.

It may not change connector order, GPIO assignments, power-net identity, or stock-circuit dispositions without reopening the relevant Task 2 subtask.

---

## Completion gate

The final Task 2F CI gate verifies:

- Task 2A source audit passes;
- Task 2B source audit passes;
- Task 2C source audit passes;
- Task 2D composed net contract passes;
- Task 2E firmware ownership audit passes;
- SW22/D22 and RGB bypass match the source;
- GP1 split is preserved;
- GP4 J1.3 isolation is source-verified;
- all seven connector pins match the frozen contract;
- SPI GPIO and firmware ownership agree;
- MOTION has no PCB or firmware owner;
- VCC/GND mapping is exact;
- retained RGB/matrix/encoder GPIO ownership is exact;
- legacy conflicting peripheral ownership is retired;
- final GPIO ownership contains no unresolved conflict.

**Task 2F: COMPLETE.**

**Task 2: COMPLETE — electrical/firmware interface locked.**

**Next task: Task 3 — create the right-hand trackball PCB derivative.**
