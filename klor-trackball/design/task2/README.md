# Task 2 — Electrical and Firmware Interface

Status: **COMPLETE**

Task 2 converts the KLOR trackball electrical concept into a source-backed implementation contract for the right-hand PCB derivative and the later QMK trackball firmware.

Dependency chain:

```text
2A → 2B → 2C → 2D → 2E → 2F
```

All six subtasks are complete. The final Task 2F audit rebuilds the earlier source audits and reports:

```text
unresolved GPIO conflicts: 0
unresolved net conflicts: 0
```

Task 3 is authorized to create the right-hand trackball PCB derivative against this frozen contract.

Task 2 itself does **not** modify production PCB or production firmware files. It determines exactly what those later implementation tasks must change.

---

## What Task 2 accomplished

Before Task 2, the project had a proposed PMW3360 pin assignment and a known requirement to remove the rightmost Konrad thumb key. Important implementation details were still unresolved:

- what logical R34 corresponded to in KiCad;
- which diode and RGB device belonged to that key;
- how deleting that key affected the matrix and RGB chain;
- what stock functions already owned GP2, GP3, GP4, and GP9;
- whether GP4 was physically connected to the TRRS jack;
- the exact Kivipallur connector pin order and mating orientation;
- whether the KLOR supply net was actually named 3V3;
- which QMK features would conflict with PMW3360 ownership;
- whether the complete electrical + firmware plan had any hidden GPIO or net conflict.

Task 2 resolved each of these from the checked-in KiCad, Klorball35/Kivipallur, and QMK sources.

---

## 2A — Removed-key circuit audit

Logical **R34** is not a KiCad resistor reference. It is the Konrad logical key position implemented by PCB footprint `SW22`. Its associated matrix diode is `D22`.

The stock matrix path is:

```text
col1 → SW22 → Net-(D22-A) → D22 → row3
```

Task 3 must remove `SW22` and `D22`, delete the obsolete local `Net-(D22-A)` copper, preserve the `col1` and `row3` trunks, and **not bridge `col1` and `row3`**.

### RGB consequence

`SW22` is a combined MX + SK6812 footprint. The RGB data chain around it is:

```text
SW13 DOUT → SW22 DIN → SW22 DOUT → SW14 DIN
```

Deleting SW22 therefore requires the permanent copper bypass:

```text
SW13 DOUT → SW14 DIN
```

SW22's VCC/GND connections are ordinary shared rails. Only SW22-local branches are removed; shared rail continuity must be preserved.

Detailed evidence: [`TASK2A_RESULT.md`](TASK2A_RESULT.md).

---

## 2B — GPIO ownership and split/TRRS audit

The proposed PMW3360 GPIOs were traced through both the stock QMK configuration and actual PCB copper.

| GPIO | Stock ownership | Revision-1 ownership | Required disposition |
| --- | --- | --- | --- |
| GP1 | split serial / `TX → J1.4` | split serial | preserve |
| GP2 | SDA / I2C1 / PAW3204 SDIO | PMW3360 SCK | retire stock I2C/PAW3204 ownership |
| GP3 | SCL / I2C1 / PAW3204 SCLK | PMW3360 MOSI | retire stock I2C/PAW3204 ownership; J2 haptic DNP |
| GP4 | RX / optional full-duplex split / `J1.3` | PMW3360 MISO | physically isolate J1.3 |
| GP9 | AUDIO / BZ1 | PMW3360 CS | retire audio ownership; BZ1 inactive/DNP |

### GP4 / TRRS finding

GP4 is not only a firmware conflict. The stock PCB physically connects the `RX` net to TRRS contact `J1.3`.

The exact stock segment to remove in Task 3 is:

```text
net: RX (28)
layer: F.Cu
width: 0.254 mm
from: (92.700, 127.025)
to:   (90.880, 127.025)
```

After that change:

```text
J1.3 = NC
GP4 = PMW_MISO only
```

The actual split transport remains:

```text
GP1 → TX → J1.4
mode: half-duplex
```

Firmware-only disabling of full duplex is not sufficient; the GP4-to-J1.3 copper isolation is mandatory.

The legacy reversible/I2C solder-jumper paths must remain open. `J2.3` is directly tied to SCL, so the right-side haptic module must be DNP for revision 1.

Detailed evidence: [`TASK2B_RESULT.md`](TASK2B_RESULT.md).

---

## 2C — Kivipallur connector and orientation

The Kivipallur breakout uses a 1×7, 2.54 mm vertical through-hole header.

Breakout-side numbering is:

```text
1 GND
2 +3V3
3 MOTION
4 SCK
5 MOSI
6 MISO
7 CS
```

The proven Klorball35 keyboard-side mate deliberately reverses that order because the connectors mate opposite-facing:

```text
1 CS
2 MISO
3 MOSI
4 SCK
5 NC
6 +3V3
7 GND
```

The mating rule is:

```text
Kivipallur breakout pin N ↔ KLOR keyboard pin (8 − N)
```

Do **not** copy Kivipallur's numbering directly onto the KLOR-side connector.

### Locked KLOR connector orientation

Against the canonical KLOR Gerber/Excellon frame:

- connector side: `F.Cu`;
- connector row axis: global Y;
- pin 1: negative-Y end;
- pin 7: positive-Y end;
- row order from negative Y to positive Y: `CS, MISO, MOSI, SCK, NC, 3V3, GND`;
- connector lies on the positive-X / non-sensor side of the breakout guide;
- breakout service direction: negative X;
- Task 1 breakout datum: `(143.111, -134.748)`.

The Klorball35 2×22 mm rectangle is on `Cmts.User`. It is a mechanical insertion/orientation guide, **not an actual fabricated Edge.Cuts slot**. Task 3 must create the real KLOR PCB pass-through or edge clearance.

Detailed evidence: [`TASK2C_RESULT.md`](TASK2C_RESULT.md).

---

## 2D — PCB net contract

Task 2D combined the GPIO audit with the physical connector contract and froze the final derivative net names.

| KLOR pin | Breakout pin | Signal | Final KLOR PCB net | MCU / U1 pad |
| ---: | ---: | --- | --- | --- |
| 1 | 7 | CS | `PMW_CS` | GP9 / U1.12 |
| 2 | 6 | MISO | `PMW_MISO` | GP4 / U1.7 |
| 3 | 5 | MOSI | `PMW_MOSI` | GP3 / U1.6 |
| 4 | 4 | SCK | `PMW_SCK` | GP2 / U1.5 |
| 5 | 3 | MOTION | **NC** | none |
| 6 | 2 | +3V3 | `VCC` | U1.21 |
| 7 | 1 | GND | `GND` | U1 ground rail |

The reassigned SPI signals use semantic derivative net names: `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, and `PMW_SCK`. The stock names `AUDIO`, `RX`, `SCL`, and `SDA` describe the source topology being replaced and must not remain as the final PMW signal names.

### Power-net correction

Earlier planning called the KLOR-side power net `3V3`. The actual stock KLOR source uses `VCC`. With the selected Elite-Pi controller this is the 3.3 V controller rail.

The frozen power contract is:

```text
Kivipallur +3V3 → KLOR VCC
Kivipallur GND  → KLOR GND
```

Task 3 must not create a second KLOR `3V3` rail merely to mirror the breakout label.

Detailed evidence: [`TASK2D_RESULT.md`](TASK2D_RESULT.md).

---

## 2E — QMK firmware ownership

Task 2E audited the stock keyboard-level QMK configuration, both checked-in keymaps, and the ChibiOS HAL/peripheral configuration.

The revision-1 GPIO ownership is:

| GPIO | Firmware owner |
| --- | --- |
| GP0 | WS2812 / RGB matrix |
| GP1 | half-duplex split serial |
| GP2 | PMW3360 SCK |
| GP3 | PMW3360 MOSI |
| GP4 | PMW3360 MISO |
| GP5 / GP6 / GP7 / GP8 | matrix rows |
| GP9 | PMW3360 CS |
| GP20 / GP21 / GP22 / GP23 / GP26 / GP27 | matrix columns |
| GP28 / GP29 | encoder |

There is one revision-1 owner per GPIO.

### PMW3360 QMK contract

The trackball firmware derivative must implement the equivalent of:

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

MOTION is intentionally unused, so revision 1 must not define `POINTING_DEVICE_MOTION_PIN`.

The trackball build disables or removes ownership for OLED, haptic, audio, music, stock PAW3204, I2C1, and audio PWM4. The stock default and Vial keymap `rules.mk` files both explicitly re-enable OLED/audio/haptic behavior, so neither may be reused unchanged.

Target ChibiOS peripheral state:

```text
HAL_USE_SPI      = TRUE
RP_SPI_USE_SPI0  = TRUE

HAL_USE_I2C      = FALSE
RP_I2C_USE_I2C1 = FALSE

HAL_USE_PWM      = FALSE
RP_PWM_USE_PWM4  = FALSE
```

Pointer rotation/inversion, CPI, lift-off distance, scrolling, acceleration, and auto-mouse behavior are intentionally deferred to Task 7 hardware bring-up.

Detailed evidence: [`TASK2E_RESULT.md`](TASK2E_RESULT.md).

---

## 2F — Final interface freeze

Task 2F is the integration gate for all of Task 2. Its CI workflow regenerates the 2A, 2B, 2C, 2D, and 2E JSON evidence directly from source and verifies that the full connector/net/GPIO/firmware contract agrees end to end.

The final authoritative interface is:

| KLOR pin | Kivipallur pin | Signal | PCB net | MCU / U1 | Firmware function | Required stock change |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 7 | CS | `PMW_CS` | GP9 / U1.12 | PMW3360 CS | disable audio/music + PWM4; BZ1 inactive/DNP |
| 2 | 6 | MISO | `PMW_MISO` | GP4 / U1.7 | SPI0 MISO | remove verified RX branch to `J1.3`; J1.3 NC |
| 3 | 5 | MOSI | `PMW_MOSI` | GP3 / U1.6 | SPI0 MOSI | disable I2C1/PAW3204; J2 haptic DNP; jumpers open |
| 4 | 4 | SCK | `PMW_SCK` | GP2 / U1.5 | SPI0 SCK | disable I2C1/PAW3204; jumpers open |
| 5 | 3 | MOTION | **NC** | none | unused / polling | leave connector pad unrouted; no motion GPIO |
| 6 | 2 | +3V3 | `VCC` | U1.21 | 3.3 V supply | use existing KLOR VCC |
| 7 | 1 | GND | `GND` | ground rail | ground | use existing KLOR GND |

Task 2F also confirms the required non-connector changes:

- remove `SW22` and `D22`;
- delete the obsolete local diode stub;
- do not bridge the matrix nets;
- bypass the RGB chain as `SW13 DOUT → SW14 DIN`;
- preserve `GP1 → TX → J1.4` half-duplex split;
- physically isolate `J1.3` from GP4;
- keep optional I2C jumpers open;
- keep J2 haptic DNP;
- keep BZ1 inactive/DNP;
- maintain the Task 2C connector side and handedness;
- create the real breakout pass-through in Task 3;
- preserve final RGB counts of 20 left / 19 right / 39 total.

Detailed final contract: [`TASK2F_RESULT.md`](TASK2F_RESULT.md).

---

## Final Task 2 implementation contract for Task 3

Task 3 may now create the right-hand trackball PCB derivative. It must:

1. remove `SW22` and `D22`;
2. remove only their obsolete/local matrix copper while preserving `col1` and `row3`;
3. add the permanent `SW13 DOUT → SW14 DIN` RGB bypass;
4. add the 1×7 KLOR-side Kivipallur connector with the frozen orientation and reversed mating order;
5. route `PMW_CS`, `PMW_MISO`, `PMW_MOSI`, and `PMW_SCK`;
6. connect breakout +3V3 to existing KLOR `VCC`;
7. connect breakout GND to existing `GND`;
8. leave MOTION unconnected;
9. remove the exact GP4/RX branch to `J1.3`;
10. preserve GP1 `TX → J1.4` split transport;
11. leave the legacy I2C jumpers open and J2 haptic DNP;
12. leave BZ1 inactive/DNP;
13. create the actual fabricated breakout pass-through or edge clearance at the Task 1 datum;
14. preserve R32, R33, the right encoder, and all unaffected stock circuitry.

Task 3 may determine local routing geometry, trace/via placement, obsolete-copper cleanup, and final connector XY consistent with the locked mechanical/service constraints.

Task 3 may **not** change connector order, GPIO assignment, PMW net names, VCC/GND mapping, MOTION disposition, split/TRRS disposition, or optional-feature ownership without explicitly reopening the relevant Task 2 subtask.

---

## What remains deferred

Task 2 does not implement:

- production PCB routing or cutouts — Task 3;
- switchplate modifications — Task 4;
- right-case shell relief — Task 5;
- integrated final mechanical/PCB validation — Task 6;
- actual trackball QMK firmware — Task 7;
- PMW3360 CPI/orientation/scrolling tuning — Task 7;
- fabrication and hardware bring-up — Task 8.

The project as a whole is therefore **not fabrication-locked** even though Task 2 is complete.

---

## Verification and evidence

Machine-readable contract:

- [`task2_manifest.yaml`](task2_manifest.yaml)

Subtask results:

- [`TASK2A_RESULT.md`](TASK2A_RESULT.md)
- [`TASK2B_RESULT.md`](TASK2B_RESULT.md)
- [`TASK2C_RESULT.md`](TASK2C_RESULT.md)
- [`TASK2D_RESULT.md`](TASK2D_RESULT.md)
- [`TASK2E_RESULT.md`](TASK2E_RESULT.md)
- [`TASK2F_RESULT.md`](TASK2F_RESULT.md)

Audit scripts:

- `audit_task2a_removed_key.py`
- `audit_task2b_gpio_trrs.py`
- `audit_task2c_kivipallur_connector.py`
- `audit_task2d_pcb_net_contract.py`
- `audit_task2e_firmware_ownership.py`
- `audit_task2f_interface_freeze.py`

CI workflow:

- `.github/workflows/klor-task2f-interface-freeze.yml`

After Task 2 was frozen, the earlier per-subtask 2A–2E workflow files were removed as redundant. Their audit scripts and result documents remain checked in. The final 2F workflow is the regression gate: it rebuilds and runs all six Task 2 audits in dependency order before passing.

The final 2F gate passes only when the source-backed evidence remains mutually consistent.

---

## Downstream status

Task 2 is closed and remains a locked input to later work. Task 3 has since progressed through **3E**; current project status and the next active subtask are maintained in the [project README](../../README.md) and [Task 3 README](../task3/README.md).

Reopen Task 1 or Task 2 only if later implementation uncovers a hard constraint that invalidates a verified assumption.
