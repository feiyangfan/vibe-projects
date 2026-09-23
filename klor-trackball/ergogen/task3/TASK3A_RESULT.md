# Task 3A Result — Electrical Architecture

## Status

**PASS — Task 3A is complete and the Rev-1 electrical architecture is frozen.**

Task 3A freezes the electrical architecture that Tasks 3B–3E must implement. It deliberately does not create production footprints or route copper.

## Controller selection

Rev 1 selects **0xCB Helios rev1.0** as the production controller.

Audited upstream source:

- repository: `0xCB-dev/0xCB-Helios`;
- commit: `e1a25eb5e4b1bcb25e13dcb18bd6e841dcf7be11`.

Reasons:

- open hardware and source-auditable;
- RP2040 Pro-Micro drop-in family;
- all required KLOR matrix/encoder/split GPIOs are exposed;
- GP2/GP3/GP4 are a natural SPI0 SCK/TX/RX grouping for PMW3360;
- explicit 3.3 V output is exposed;
- RAW/5 V is exposed;
- GP25 is exposed through the controller's onboard 3.3 V → 5 V level shifter for addressable RGB.

Task 3B still owns physical footprint qualification inside the frozen U1 envelope. Failure of that qualification reopens Task 3A; it does not authorize moving U1.

## Final GPIO contract

| Function | GPIO |
| --- | --- |
| Split data | GP1 |
| PMW SCK, right only | GP2 |
| PMW MOSI, right only | GP3 |
| PMW MISO, right only | GP4 |
| Matrix row 0 | GP5 |
| Matrix row 1 | GP6 |
| Matrix row 2 | GP7 |
| Matrix row 3 | GP8 |
| PMW CS, right only | GP9 |
| Matrix col 3 | GP20 |
| Matrix col 5 | GP21 |
| Matrix col 2 | GP22 |
| Matrix col 4 | GP23 |
| RGB data | GP25 through Helios onboard 5 V level shifter |
| Matrix col 1 | GP26 |
| Matrix col 0 | GP27 |
| Encoder | GP28 / GP29 |

Left does not connect GP2/GP3/GP4/GP9 to peripherals.

## Power domains

Three board-level rails are explicit:

- `RAW_5V` — SK6812 VDD and split power;
- `V3V3` — PMW3360 breakout input on the right;
- `GND`.

Helios rev1.0 pad 30 is the RAW/5 V pin. With its default JP2 1–2 bridge, RAW is tied into the controller's local +5 V input domain, which feeds the onboard 3.3 V regulator and RGB level shifter.

Helios pad 27 supplies regulated 3.3 V to PMW header pin 6.

The split assumes **one USB power source while the halves are connected**. Powered TRRS hot-plug is not a supported use case.

## RGB electrical decision

Rev 1 uses the 12 mA-class SK6812MINI-E production reference on a 5 V rail.

Unlike the historical KLOR GP0 direct-drive arrangement, Rev 1 uses:

```text
RP2040 GP25
    ↓
Helios onboard 74LVC1T45
    ↓
Helios pad 32 / 5 V RGB data
    ↓
SK6812 chain
```

This gives the LEDs a 5 V data signal while they are powered from `RAW_5V`.

The left chain has 20 devices. The right chain has 19 and bypasses SW22/R34 logically.

Full-white/unrestricted brightness is not assumed to fit a USB power budget. Firmware brightness limiting is mandatory and the final cap is deferred to firmware/integration validation.

## Matrix contract

The stock four-row / six-column local matrix is retained:

- rows: GP5, GP6, GP7, GP8;
- columns: GP27, GP26, GP22, GP20, GP23, GP21;
- direction: `COL2ROW`.

The product count of 39 refers to **MX keys**. Encoder push switches are additional matrix switch positions:

- left: 20 MX + encoder push = 21 active matrix positions;
- right: 19 MX + encoder push = 20 active matrix positions;
- combined split firmware: 41 active switch positions.

The encoder push remains row3/col5 on both halves.

SW19 is absent on both fixed-Konrad production boards. SW22 is present only on the left; the right omits SW22/D22.

## Encoder contract

Both EC11 rotary functions and both push switches are retained.

Left rotary:

- A = GP28;
- B = GP29.

Right rotary:

- A = GP29;
- B = GP28.

The right reversal retains the established QMK direction semantics.

## Split contract

TRRS is:

| Pin | Net |
| ---: | --- |
| 1 | RAW_5V |
| 2 | GND |
| 3 | NC |
| 4 | SPLIT_DATA / GP1 |

Transport is half-duplex serial. Full-duplex RX is removed.

## PMW3360 contract

Right side only:

| Signal | GPIO | Helios pad |
| --- | --- | ---: |
| SCK | GP2 | 6 |
| MOSI | GP3 | 7 |
| MISO | GP4 | 8 |
| CS | GP9 | 13 |

MOTION remains NC and firmware will poll the sensor.

The keyboard-side 1x7 physical order remains the frozen Task-2D order:

`CS, MISO, MOSI, SCK, NC/MOTION, 3V3, GND`.

## Removed electrical baggage

Rev 1 does not allocate footprints, nets, or GPIO ownership to:

- OLED;
- haptic;
- buzzer/audio;
- PAW3204;
- general I2C accessories;
- battery connectors/operation;
- power switch;
- full-duplex RX;
- alternate-layout SW19.

## Boundary

Task 3A does **not** choose routing.

Task 3B now owns production footprint qualification. Tasks 3C/3D consume this contract to generate the left/right unrouted boards. Task 3E validates the pair.


## Freeze evidence

Passing source head:

`5e3606a35321714066d90563f36950cab9cb2c35`

GitHub Actions:

- workflow: `KLOR Task 3A - electrical contract`;
- run ID: `35833410675`;
- job ID: `107091064957`;
- conclusion: **success**.

The regression proves:

- Task-2D remains frozen at 20/19/39 MX keys;
- Helios rev1.0 controller selection and audited pad contract are exact;
- power domains and TRRS safety assumptions are explicit;
- matrix sites derive from the stock KLOR PCB;
- 39 MX + 2 encoder-push matrix positions are accounted for;
- encoder direction/push contracts are exact;
- half-duplex split is exact;
- left/right RGB chains derive from stock topology with SW19 removed and right SW22 bypassed;
- Kivipallur numbering and reversed keyboard-side connector order match;
- GPIO ownership is unique on each half;
- PMW GPIO ownership exists only on the right;
- removed Rev-1 features own no electrical interface;
- routing remains outside Task 3.

## Next

Proceed to **Task 3B — qualify production footprints**.
