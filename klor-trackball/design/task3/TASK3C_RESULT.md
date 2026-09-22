# Task 3C result — destructive PCB synchronization

Status: **COMPLETE**.

Task 3C synchronizes the frozen Task 3B schematic contract onto the derivative PCB and performs the already-authorized destructive stock-board edits.

The board is now electrically prepared for the trackball interface, but **J4 is deliberately not final-placed and PMW3360 signals are not routed to J4 yet**. Mechanical placement/pass-through work belongs to Task 3D; J4-to-U1 routing belongs to Task 3E.

## Scope

Modified production source:

```text
PCB/konrad_trackball/konrad_trackball.kicad_pcb
```

Authoritative schematic remains unchanged from Task 3B:

```text
PCB/konrad_trackball/konrad_trackball.kicad_sch
```

Stock source remains unchanged:

```text
klor1.4/PCB/klor1_4/
```

Task 3C PCB blob:

```text
c3fefdb583d653a836d2ab99a9d94126ea331a3b
```

Task 3B schematic blob retained exactly:

```text
4239dd2f139be30e24ee7109800a5ae9f179aee3
```

## Removed R34 physical circuit

The derivative PCB no longer contains:

- `SW22`;
- `D22`;
- the local `Net-(D22-A)` net;
- the `col1` branch that served only SW22;
- the `row3` branch from retained D21 toward removed D22.

The retained matrix trunks remain separate:

```text
col1 = net 17
row3 = net 38
```

The audit explicitly verifies retained `col1` ownership on other switches and retained `row3` through D21.

## RGB bypass implemented in copper

The old two-net topology:

```text
SW13 DOUT -> SW22 DIN
SW22 DOUT -> SW14 DIN
```

is now one physical net:

```text
SW13 DOUT -> SW14 DIN
```

Both SW13 DOUT and SW14 DIN are assigned to:

```text
net 76 = Net-(SW13B-DOUT)
```

The obsolete `Net-(SW14B-DIN)` / net 77 is retired.

The retained routes are joined by one new B.Cu splice:

| Property | Value |
| --- | --- |
| UUID | `3c3c0005-0000-4000-8000-000000000001` |
| start | `(148.115, 131.730)` |
| end | `(148.109492, 133.815508)` |
| width | 0.254 mm |
| layer | B.Cu |
| net | 76 / `Net-(SW13B-DOUT)` |

The splice is deliberately around global/KiCad X ≈ 148.1, rather than crossing the deleted SW22 area near the future breakout datum at X ≈ 143.1.

## MCU ownership synchronized to PCB

The physical U1 socket pads now use the Task 2/3B semantic PMW nets:

| GPIO | U1 pad | PCB net |
| --- | ---: | --- |
| GP2 | 5 | `PMW_SCK` |
| GP3 | 6 | `PMW_MOSI` |
| GP4 | 7 | `PMW_MISO` |
| GP9 | 12 | `PMW_CS` |

New net IDs are:

| Net ID | Name |
| ---: | --- |
| 82 | `PMW_CS` |
| 83 | `PMW_MISO` |
| 84 | `PMW_MOSI` |
| 85 | `PMW_SCK` |

Only the reversible U1 socket cross-connect copper is retained on those four nets at this stage. Each PMW signal currently has exactly three retained U1 cross-connect segments and **zero PMW vias**.

The old optional `AUDIO`, `SDA`, and `SCL` nets remain on their legacy optional circuitry but no longer own the MCU pins.

## TRRS / GP4 isolation

The obsolete `RX` PCB net is retired completely.

J1 pad 3 is now physically **no-net** on both reversible pad copies.

The old GP4-to-J1.3 copper, including the Task 2B-verified adjacent segment, is removed.

The active split transport remains unchanged:

```text
GP1 -> TX -> J1.4
```

Net 31 / `TX` is preserved.

## J4 introduced, but deliberately not final-placed

Task 3C adds the PCB footprint matching the Task 3B schematic symbol:

```text
Reference: J4
Footprint: Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical
Side: F.Cu
```

Pin contract:

| J4 pin | PCB state |
| ---: | --- |
| 1 | `PMW_CS` |
| 2 | `PMW_MISO` |
| 3 | `PMW_MOSI` |
| 4 | `PMW_SCK` |
| 5 | NC / MOTION |
| 6 | `VCC` |
| 7 | `GND` |

### Staging placement

J4 is temporarily parked at:

```text
KiCad XY = (60.0, 70.0)
rotation = 0°
side = F.Cu
```

The stock board Edge.Cuts X range begins at approximately 70.828615 mm, so this staging position is fully off-board by design.

**This is not a production connector location.**

Task 3D exclusively owns:

- final J4 XY;
- final J4 rotation;
- the fabricated breakout pass-through/edge clearance;
- mechanical clearance verification.

Task 3D must preserve the already-locked Task 2C handedness and pin order.

## Board outline and retained hardware

Task 3C makes **no Edge.Cuts change**.

The audit proves the derivative Edge.Cuts are byte-for-byte equivalent to the stock Edge.Cuts primitives.

It also proves:

- every retained stock footprint keeps the exact stock XY, rotation, and side;
- every untouched retained footprint block is unchanged;
- U1, J1, and SW14 differ only in the explicitly authorized pad-net assignments;
- every retained stock trace keeps the exact stock geometry/layer/width;
- every retained stock via keeps the exact stock geometry;
- all trace/via net changes are within the authorized Task 3C set;
- J2, OLED1, and BZ1 remain physically present;
- legacy optional nets remain present but no longer own GP2/GP3/GP9.

The physical PCB transformation removes 65 stock copper segments and 5 stock vias and adds one RGB bridge segment. Those removals are exactly enumerated and regression-checked by the Task 3C audit.

## Reproducible transformation

Task 3C retains the deterministic transformation script:

```text
design/task3/apply_task3c_pcb_sync.py
```

The script deterministically transforms the exact Task 3B PCB baseline.

A temporary GitHub Actions write workflow was used once to execute that transform and commit the generated PCB inside GitHub. That write workflow was then removed.

The retained script is reproducibility evidence, not an ongoing mutation mechanism.

## Verification

Canonical audit:

```text
design/task3/audit_task3c_pcb_sync.py
```

Active CI:

```text
.github/workflows/klor-task3c-pcb-sync-audit.yml
```

Passing run:

```text
run id: 35361283393
head: f2d43b674ac34fa4060783f0a7138e5a2fdcdd5c
artifact: klor-task3c-pcb-sync-audit
artifact id: 10555015081
digest: sha256:963ae1ad6ed04cb7ac1789d880ab7336c324c5db66162d518b78fe5bcbc2ddf7
```

All audit checks pass, including:

- stock PCB/schematic source hashes locked;
- Task 3B schematic unchanged;
- exact Task 3C PCB blob locked;
- SW22/D22 absent;
- net table exact;
- U1 PMW ownership exact;
- J1.3 no-net and J1.4/TX preserved;
- J4 pin contract exact;
- J4 staged off-board on F.Cu;
- stock Edge.Cuts exact;
- authorized segment/via deletion sets exact;
- retained trace/via geometry unchanged;
- PMW U1 cross-connect set exact;
- RGB bypass exact;
- retained matrix trunks and optional hardware preserved.

## Boundary after 3C

At the end of 3C:

- destructive stock-PCB cleanup is complete;
- PCB semantic net ownership matches the 3B schematic;
- J4 exists with the correct electrical pin contract;
- PMW nets are **not yet routed from U1 to J4**;
- J4 is **not yet mechanically placed**;
- no breakout pass-through exists yet;
- board edges remain stock.

Therefore Task 3C does not claim final DRC or fabrication readiness.

**Task 3C: COMPLETE.**

Next: **Task 3D — place J4 at the locked mechanical interface and create the manufacturable breakout pass-through/edge clearance.**


## Representation normalization

Task 3C was reworked onto the normalized Task 3B PCB baseline. Only regenerable KiCad `filled_polygon` cache data is omitted; the Task 3C physical/electrical edits are unchanged. The normalized Task 3C PCB blob is `c3fefdb583d653a836d2ab99a9d94126ea331a3b`.
