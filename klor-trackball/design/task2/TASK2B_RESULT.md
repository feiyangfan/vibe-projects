# Task 2B result — GPIO ownership and split/TRRS audit

Status: **complete**.

Task 2B audits the stock KLOR 1.4 QMK configuration and the actual KiCad PCB copper for the GPIOs proposed for the PMW3360. It does not modify the production PCB or firmware. Its purpose is to lock which stock paths must be preserved, disabled, left open, or physically isolated before Task 3 routing begins.

## Sources

- `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json`
- `design/task2/audit_task2b_gpio_trrs.py`
- `.github/workflows/klor-task2b-gpio-trrs-audit.yml`

The Task 2B CI audit passes every locked source-topology assertion.

## Stock firmware ownership

The stock Elite-Pi build currently claims the proposed PMW pins as follows:

| GPIO | Stock firmware use | Task 2 target |
| --- | --- | --- |
| GP1 | active half-duplex split serial TX | preserve split serial |
| GP2 | I2C1 SDA + PAW3204 SDIO | PMW3360 SCK |
| GP3 | I2C1 SCL + PAW3204 SCLK | PMW3360 MOSI |
| GP4 | commented optional full-duplex serial TX | PMW3360 MISO |
| GP9 | audio | PMW3360 CS |

The stock `keyboard.json` also enables OLED, haptic, and audio while pointing-device support is disabled. Those stock feature settings cannot remain unchanged in the trackball firmware variant.

## Source-backed PCB topology

The stock U1/controller nets relevant to Task 2B are:

| GPIO | U1 socket pad | Stock PCB net | Direct/important peers |
| --- | ---: | --- | --- |
| GP1 | 2 | `TX` (net 31) | `J1.4` only |
| GP2 | 5 | `SDA` (net 6) | open I2C/reversible jumpers |
| GP3 | 6 | `SCL` (net 7) | open I2C/reversible jumpers + `J2.3` |
| GP4 | 7 | `RX` (net 28) | `J1.3` only |
| GP9 | 12 | `AUDIO` (net 2) | `BZ1.1` only |

The duplicated physical U1 pads are part of the stock reversible footprint; the audited target pad instances for each GPIO carry the same electrical net.

## GP1 — preserve half-duplex split transport

Stock GP1 is the active half-duplex split-serial pin and is connected through PCB net `TX` directly to TRRS connector `J1` pad 4.

Locked disposition:

- preserve GP1;
- preserve the `TX` path to `J1.4`;
- keep half-duplex split transport for revision 1;
- do not repurpose or cut this path while freeing GP4.

This means the trackball edit must isolate only the unused full-duplex contact, not the active split conductor.

## GP4 — exact TRRS isolation

Stock GP4 is available in firmware only as the commented optional full-duplex serial TX pin. On the PCB its socket pad is net `RX`, whose only external peer is TRRS `J1.3`.

The source audit verifies the exact J1-adjacent copper branch:

```text
net: RX (28)
layer: F.Cu
width: 0.254 mm
from: (92.700, 127.025)
to:   (90.880, 127.025)
```

Locked disposition for the right-hand trackball derivative:

1. keep the physical TRRS connector because GP1/J1.4 is still required;
2. make `J1.3` electrically NC;
3. remove the verified F.Cu branch above from `J1.3` into the `RX` net;
4. retain U1 pad 7 / GP4 for the new PMW3360 MISO route;
5. do not enable full-duplex split firmware on the trackball variant.

This is the required physical isolation point. Firmware configuration alone is not sufficient on the stock PCB because `J1.3` is directly wired to the GP4 net.

## GP2 / GP3 — retire stock I2C and PAW3204 ownership

Stock firmware assigns:

- GP2 = `I2C1_SDA_PIN` and `PAW3204_SDIO_PIN`;
- GP3 = `I2C1_SCL_PIN` and `PAW3204_SCLK_PIN`.

The PCB audit confirms the corresponding nets are `SDA` and `SCL`.

### Optional I2C paths

The legacy OLED/reversible peripheral paths are controlled through solder jumpers whose checked-in footprint is the **open** variant. The audit verifies the I2C-connected jumpers are default-open.

Examples include:

- OLED/reversible paths: `JP3`, `JP4`, `JP5`, `JP6`;
- J3/reversible paths: `JP16`, `JP17`, `JP20`, `JP21`;
- haptic-side SDA paths: `JP27`, `JP28`.

`J2.3` is directly on `SCL`, so the haptic module itself must not be populated on the trackball right half.

Locked disposition:

- GP2 becomes PMW3360 SCK;
- GP3 becomes PMW3360 MOSI;
- disable stock I2C use on GP2/GP3 in the trackball firmware;
- disable the PAW3204 path;
- keep all legacy I2C/reversible solder jumpers open;
- do not populate the right OLED/haptic optional hardware for revision 1;
- specifically, do not populate `J2` haptic hardware because `J2.3` is hardwired to the former SCL net;
- Task 3 may prune obsolete unpopulated branch copper/footprints where useful for routing or mechanical clearance, but must not reconnect a legacy load to GP2/GP3.

No hardwired pull-up or active device was found directly on GP2/SDA or GP3/SCL by this pad/net audit; the directly connected non-jumper exception is the unpopulated `J2.3` haptic connection on SCL.

## GP9 — retire audio

Stock firmware assigns `AUDIO_PIN GP9`. The PCB audit resolves GP9 to net `AUDIO`, whose only peer is buzzer `BZ1.1`.

Locked disposition:

- GP9 becomes PMW3360 CS;
- disable QMK audio in the trackball firmware variant;
- do not populate `BZ1` on the right trackball derivative;
- Task 3 should remove the obsolete `AUDIO` branch/footprint where it conflicts with the new CS route or trackball geometry; it must not leave an active buzzer load on GP9.

## Locked ownership after Task 2B

| GPIO | Revision-1 owner | Required stock-path disposition |
| --- | --- | --- |
| GP1 | split serial | preserve `TX -> J1.4` |
| GP2 | PMW3360 SCK | disable I2C/PAW3204; legacy I2C jumpers open |
| GP3 | PMW3360 MOSI | disable I2C/PAW3204; J2 DNP; legacy I2C jumpers open |
| GP4 | PMW3360 MISO | disconnect `J1.3` using verified F.Cu branch |
| GP9 | PMW3360 CS | disable audio; BZ1 DNP/no active audio load |

The retained matrix, RGB data pin GP0, and encoder pins are not reassigned by this Task 2B contract.

## Completion gate

Task 2B passes:

- stock QMK ownership of GP1/GP2/GP3/GP4/GP9 is resolved;
- GP1 half-duplex split path is source-verified and preserved;
- GP2/GP3 I2C + PAW3204 conflicts have explicit disabled/open/DNP dispositions;
- the direct `J2.3` SCL connection is accounted for;
- GP4's only external peer is `J1.3`;
- the exact F.Cu branch for GP4/TRRS isolation is verified in source;
- GP9's only external peer is `BZ1.1` and audio disposition is explicit;
- every proposed PMW GPIO has one revision-1 owner.

**Task 2B: COMPLETE.**

Next dependency: **Task 2C — lock the Kivipallur physical/electrical connector.**
