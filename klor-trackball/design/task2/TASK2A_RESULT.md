# Task 2A result — removed-key circuit audit

Status: **complete**.

Task 2A audits the stock KLOR 1.4 schematic and PCB around logical Konrad key **R34**, which is implemented by PCB reference `SW22`.

No production PCB geometry is modified by this task. The purpose is to lock the electrical disposition that Task 3 must implement.

## Source files

- `klor1.4/PCB/klor1_4/klor1_4.kicad_sch`
- `klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`

Reproducible audit:

- `design/task2/audit_task2a_removed_key.py`
- `.github/workflows/klor-task2a-electrical-audit.yml`

The Task 2A CI audit passes all source-resolution checks.

## Naming clarification

`R34` is the logical Konrad right-thumb key position. It is **not** a KiCad resistor reference.

The actual PCB/schematic component reference is `SW22`.

## SW22 is a combined switch + RGB device

The stock schematic represents `SW22` as the two units of:

`KLORlib:SW_PUSH-MX_W_LED`

using footprint:

`KLOR:SK6812MINI_and_cherry_1`

- schematic unit 1 = MX switch
- schematic unit 2 = SK6812 RGB LED
- PCB pads 1–4 = SK6812
- PCB pads 5–6 = switch

There is therefore **no separate LED reference to remove** for R34. Removing `SW22` removes both the switch and its integrated RGB device.

## Matrix connectivity

Stock `SW22`/`D22` connectivity is:

```text
col1
  |
SW22 pad 5
SW22 switch
SW22 pad 6
  |
Net-(D22-A)
  |
D22 pad 2 / A
D22
D22 pad 1 / K
  |
row3
```

Exact source nets:

| Component pad | Net |
| --- | --- |
| `SW22.5` | `col1` |
| `SW22.6` | `Net-(D22-A)` |
| `D22.2` / A | `Net-(D22-A)` |
| `D22.1` / K | `row3` |

`Net-(D22-A)` is used only for the local SW22-to-D22 connection.

### Locked matrix disposition

For the right-hand trackball PCB derivative:

1. delete `SW22`;
2. delete `D22`;
3. delete the obsolete local `Net-(D22-A)` copper;
4. **do not bridge `col1` to `row3`**;
5. preserve the existing `col1` and `row3` trunks serving the retained keys.

If `D22` were physically left after removing `SW22`, its anode side would be floating while its cathode remained connected to `row3`. That would provide no useful keyboard function. The derivative therefore removes it rather than retaining an electrically dead stub.

## RGB connectivity

The RGB element is `SW22` unit 2 / PCB pads 1–4.

Exact stock data chain:

```text
SW13 pad 1 / DOUT
  |
Net-(SW13B-DOUT)
  |
SW22 pad 3 / DIN
SW22 SK6812
SW22 pad 1 / DOUT
  |
Net-(SW14B-DIN)
  |
SW14 pad 3 / DIN
```

Power pads:

| SW22 pad | Function | Net |
| --- | --- | --- |
| 1 | DOUT | `Net-(SW14B-DIN)` |
| 2 | VSS | `GND` |
| 3 | DIN | `Net-(SW13B-DOUT)` |
| 4 | VDD | `VCC` |

### Locked RGB disposition

Delete the SW22 RGB device with the rest of the `SW22` footprint, then make the serial RGB chain:

```text
SW13 DOUT -> SW14 DIN
```

Equivalently, the derivative must merge/bypass:

```text
Net-(SW13B-DOUT) -> Net-(SW14B-DIN)
```

There is **no logical VCC/GND bypass requirement** analogous to the RGB data chain; `VCC` and `GND` are shared rails. When Task 3 removes the SW22 footprint and its local copper, it must remove only the SW22-local power branches while preserving adjacent shared rail continuity.

## Relevant local copper

The audit records local traces/vias for all SW22/D22 nets so Task 3 can distinguish obsolete branches from retained trunks.

Relevant net IDs in the stock PCB:

| Net ID | Net |
| ---: | --- |
| 1 | `GND` |
| 3 | `VCC` |
| 17 | `col1` |
| 38 | `row3` |
| 46 | `Net-(D22-A)` |
| 76 | `Net-(SW13B-DOUT)` |
| 77 | `Net-(SW14B-DIN)` |

The matrix/data traces in this area are primarily 0.254 mm; the local VCC/GND routing is 0.381 mm.

The audit also records the duplicate reversible-footprint pad positions. Duplicate pad entries with the same pad number/ref are the front/back implementation of the reversible KLOR footprint, not separate devices.

## Nearby stock circuitry

The source audit identifies additional stock circuitry close to SW22 that is **not resolved by Task 2A** and must be handled by the next GPIO/optional-feature audit:

- `J3` at approximately 10.05 mm from the SW22 footprint origin;
- `JP17`, `JP18`, `JP19`, `JP20` at approximately 11.4 mm;
- `JP16`, `JP21` at approximately 12.2 mm;
- buzzer `BZ1` farther away at approximately 21.0 mm.

These nearby parts include I2C/optional-feature routing and are inputs to Task 2B/Task 3. Task 2A does not authorize removing them yet.

## Task 2A completion gate

The gate passes:

- `SW22` switch connectivity resolved;
- `D22` connectivity resolved;
- `D22` disposition locked: remove;
- integrated SW22 RGB device identified;
- RGB DIN source resolved to `SW13 DOUT`;
- RGB DOUT destination resolved to `SW14 DIN`;
- permanent RGB bypass locked as `SW13 DOUT -> SW14 DIN`;
- matrix nets explicitly must **not** be bridged;
- local source copper captured for Task 3 implementation.

**Task 2A: COMPLETE.**

Next dependency: **Task 2B — audit GPIO ownership and split/TRRS routing.**
