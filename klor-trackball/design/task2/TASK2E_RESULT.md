# Task 2E result — QMK firmware ownership

Status: **complete**.

Task 2E freezes firmware ownership for the KLOR Konrad PMW3360 trackball variant. It audits the stock keyboard-level QMK configuration, both checked-in keymap configurations, ChibiOS HAL/peripheral settings, and the Task 2D PCB contract.

This task does **not** implement the production firmware. Task 7 will create/build the trackball-specific firmware derivative. Task 2E defines what that derivative is allowed to enable and which GPIO/peripheral owns every relevant pin.

## Sources

- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/rules.mk`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/halconf.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/mcuconf.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keymaps/default/config.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keymaps/default/rules.mk`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keymaps/vial/config.h`
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keymaps/vial/rules.mk`
- fresh Task 2D audit evidence
- `design/task2/audit_task2e_firmware_ownership.py`
- `.github/workflows/klor-task2e-firmware-ownership-audit.yml`

## Locked GPIO ownership

The revision-1 firmware ownership map is:

| GPIO | Revision-1 owner |
| --- | --- |
| GP0 | WS2812 / RGB matrix |
| GP1 | split serial, half duplex |
| GP2 | PMW3360 SCK |
| GP3 | PMW3360 MOSI |
| GP4 | PMW3360 MISO |
| GP5 | matrix row |
| GP6 | matrix row |
| GP7 | matrix row |
| GP8 | matrix row |
| GP9 | PMW3360 CS |
| GP20 | matrix column |
| GP21 | matrix column |
| GP22 | matrix column |
| GP23 | matrix column |
| GP26 | matrix column |
| GP27 | matrix column |
| GP28 | encoder |
| GP29 | encoder |

No GPIO in this map has two revision-1 owners.

The Task 2D PMW mapping remains authoritative:

```text
SCK  -> GP2
MOSI -> GP3
MISO -> GP4
CS   -> GP9
MOTION -> NC
```

## PMW3360 / SPI QMK contract

The firmware variant must use QMK's PMW3360 pointing-device path.

Locked build/config intent:

```make
POINTING_DEVICE_ENABLE = yes
POINTING_DEVICE_DRIVER = pmw3360
SPI_DRIVER_REQUIRED = yes
```

Locked `config.h` ownership:

```c
#define SPI_DRIVER SPID0
#define SPI_SCK_PIN GP2
#define SPI_MOSI_PIN GP3
#define SPI_MISO_PIN GP4
#define PMW33XX_CS_PIN GP9

#define SPLIT_POINTING_ENABLE
#define POINTING_DEVICE_RIGHT
```

The existing ChibiOS source already has:

```c
#define HAL_USE_SPI TRUE
#define RP_SPI_USE_SPI0 TRUE
```

so the selected hardware peripheral is SPI0. GP2/GP3/GP4 are valid as the intended SPI0 SCK/TX/RX pin group for the RP2040 target.

Task 7 must explicitly override the SPI pins because the generic RP2040/Pro-Micro defaults are not the Task 2D pinout.

### MOTION is not used

Revision 1 intentionally does not route Kivipallur MOTION. Therefore the firmware must not define `POINTING_DEVICE_MOTION_PIN`.

The sensor is polled through the PMW3360 SPI driver.

### Right-side-only pointing device

Only the right half contains the sensor. The firmware must therefore use split-pointing with the device assigned to the right half:

```c
#define SPLIT_POINTING_ENABLE
#define POINTING_DEVICE_RIGHT
```

Both checked-in stock keymaps already use:

```c
#define EE_HANDS
```

Revision 1 preserves `EE_HANDS` so QMK can identify which physical half is right. The normal left/right EEPROM flashing requirement therefore remains part of firmware bring-up.

## Stock conflicts that must be removed

### GP2 / GP3 — I2C and PAW3204

Stock `config.h` claims:

```c
#define I2C1_SDA_PIN GP2
#define I2C1_SCL_PIN GP3
```

and, whenever pointing-device support is enabled, the stock block also defines:

```c
#define PAW3204_SCLK_PIN GP3
#define PAW3204_SDIO_PIN GP2
```

That block **cannot be reused** for the PMW3360 variant. Simply changing `keyboard.json` from `pointing_device: false` to `true` would activate the old PAW3204 pin declarations and create a direct ownership conflict.

The trackball variant must remove/omit:

- `I2C1_SDA_PIN GP2`
- `I2C1_SCL_PIN GP3`
- `PAW3204_SCLK_PIN GP3`
- `PAW3204_SDIO_PIN GP2`
- `I2C_DRIVER_REQUIRED = yes`

and disable the I2C1 peripheral:

```c
#define HAL_USE_I2C FALSE
#define RP_I2C_USE_I2C1 FALSE
```

This matches Task 2B's hardware rule that legacy I2C jumpers remain open and J2 haptic is DNP.

### GP4 — optional full-duplex split

Stock `config.h` documents GP4 as the optional full-duplex serial TX pin, while active split serial uses GP1 in half-duplex mode.

Revision 1 keeps:

```c
#define SERIAL_USART_TX_PIN GP1
```

and must not enable:

- `SERIAL_USART_TX_PIN GP4`
- `SERIAL_USART_RX_PIN GP1`
- `SERIAL_USART_FULL_DUPLEX`
- `SERIAL_USART_PIN_SWAP`

The physical J1.3 isolation remains a Task 3 hardware requirement from Task 2B.

### GP9 — audio/PWM

Stock `config.h` unconditionally defines `AUDIO_PIN GP9`, and stock rules select the hardware PWM audio driver.

The trackball variant must remove/omit all audio pin/driver ownership, including:

- `AUDIO_PIN GP9`
- `AUDIO_DRIVER = pwm_hardware`
- audio/music feature enables

With no revision-1 PWM feature remaining, the trackball firmware contract disables the stock audio PWM peripheral:

```c
#define HAL_USE_PWM FALSE
#define RP_PWM_USE_PWM4 FALSE
```

## Stock feature metadata that must change

Stock `keyboard.json` currently enables OLED, haptic, and audio while disabling the pointing device.

Revision-1 feature state is frozen as:

| Feature | Revision-1 state |
| --- | --- |
| bootmagic | enabled |
| encoder | enabled |
| extrakey | enabled |
| RGB matrix | enabled |
| pointing device | **enabled** |
| OLED | **disabled** |
| haptic | **disabled** |
| audio | **disabled** |
| mousekey | disabled |

The split transport must not request OLED or haptic synchronization in the trackball variant.

The stock `haptic.driver` metadata may be removed from the trackball derivative because haptics are disabled.

## Keymap-level override finding

Both checked-in stock keymaps independently re-enable conflicting features in their `rules.mk` files.

The default keymap currently enables:

```make
OLED_ENABLE = yes
AUDIO_ENABLE = yes
MUSIC_ENABLE = yes
HAPTIC_ENABLE = yes
SPLIT_HAPTIC_ENABLE = yes
```

The Vial keymap does the same.

Therefore Task 7 must **not reuse either stock keymap rules file unchanged**. A trackball-specific keymap/build must omit or explicitly disable those settings.

This is required even if keyboard-level metadata says the features are disabled, because a keymap-level Makefile assignment can re-enable the feature during the build.

## Retained ownership

The following stock assignments remain unchanged:

### Split

```text
GP1 = half-duplex serial
SERIAL_DRIVER = vendor
EE_HANDS = enabled
```

### RGB

```text
GP0 = WS2812
WS2812_DRIVER = vendor
```

Task 7 still must implement the already-locked asymmetric topology:

- left: 20 LEDs
- right: 19 LEDs
- total: 39 LEDs

Task 2E freezes GP0 ownership and the counts, but the detailed `g_led_config` mapping remains Task 7 work.

### Matrix

Rows remain:

```text
GP5 GP6 GP7 GP8
```

Columns remain:

```text
GP27 GP26 GP22 GP20 GP23 GP21
```

The physical R34/SW22 position `[7,1]` is removed from the Konrad trackball layout, but row/column GPIO ownership does not change.

### Encoder

Left side:

```text
A = GP28
B = GP29
```

Right side remains reversed as stock:

```text
A = GP29
B = GP28
```

## Deferred behavior, not ownership

Task 2E intentionally does not lock user-experience tuning that requires hardware bring-up:

- pointer X/Y rotation
- pointer axis inversion
- CPI/sensitivity
- lift-off-distance tuning
- scrolling behavior
- acceleration
- auto-mouse layer behavior

The revision-1 base contract leaves auto-mouse disabled. These behaviors may be evaluated in Task 7 after raw PMW3360 motion is confirmed.

## Required Task 7 firmware derivative

Task 7 must create a **trackball-specific firmware derivative** rather than silently changing the stock KLOR reference.

At minimum, that derivative must:

1. remove R34 from the Konrad layout;
2. implement 39-key / 20-left + 19-right RGB topology;
3. preserve GP0 RGB, GP1 split, matrix pins, encoder pins, and `EE_HANDS`;
4. enable QMK pointing-device support with the `pmw3360` driver;
5. configure SPI0 as GP2 SCK / GP3 MOSI / GP4 MISO;
6. configure PMW3360 CS as GP9;
7. enable split pointing and assign the sensor to the right half;
8. keep MOTION unused;
9. disable OLED, haptic, audio, music, I2C, and PAW3204 ownership;
10. ensure no keymap-level rules re-enable those disabled features;
11. retain `HAL_USE_SPI TRUE` and `RP_SPI_USE_SPI0 TRUE`;
12. disable unused I2C1/PWM4 peripheral ownership in the trackball variant.

## Completion gate

Task 2E passes when the audit proves:

- fresh Task 2D evidence passes;
- every retained GPIO is source-verified;
- each PMW GPIO agrees with Task 2D;
- stock GP2/GP3 I2C and PAW3204 conflicts are identified;
- stock GP4 full-duplex option is identified and remains disabled;
- stock GP9 audio conflict is identified;
- stock default/Vial keymap feature re-enables are identified;
- `EE_HANDS` is present in both stock build paths;
- SPI HAL and SPI0 are already available;
- the target feature state has one owner per GPIO;
- right-only split pointing is explicit;
- MOTION has no firmware pin owner;
- I2C1 and audio PWM ownership are retired.

**Task 2E: COMPLETE.**

Next dependency: **Task 2F — freeze the complete interface.**
