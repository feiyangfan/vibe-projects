# Task 2B Result — Preserved Stock Geometry

## Status

**PASS — Task 2B is complete.**

Task 2B reconstructs the stock KLOR 1.4 MX / fixed-Konrad geometry that the trackball design intends to preserve, before any trackball-specific delta is applied.

The active Ergogen model now treats that preserved stock geometry as a regression-tested foundation rather than as hand-copied visual reference.

## Passing source state

Branch:

`klor-trackball/task2-minimal-change`

Passing head:

`ba7cc3f96504d53f6631c60601db6e63ed2191a3`

GitHub Actions:

- workflow: `KLOR Task 2B - stock geometry`
- run ID: `35803866318`
- job ID: `107000136478`
- conclusion: **success**

Generated artifact:

- name: `klor-task2b-stock-geometry`
- artifact ID: `10726278813`
- SHA-256: `00345a889343ea0040f871cf56a7d894d17b7cfd0fc172ebc2dd1624d0969f48`

Two clean Ergogen 4.2.1 generations were diffed byte-for-byte before validation.

## Canonical frame

Task 2B uses:

- origin: stock `SW13` center;
- +X: stock KiCad +X;
- +Y: reflected from KiCad so positive Y points upward;
- rotation: reflected with the Y axis.

Task 2C will add the trackball delta in this same frame.

## Fixed-Konrad key geometry

The 20 stock fixed-Konrad switch positions are reconstructed exactly from the checked-in KiCad PCB:

- `SW1..SW17`;
- `SW20` = R32;
- `SW21` = R33;
- `SW22` = R34.

`SW19` is an alternate-layout thumb position and is explicitly excluded from the fixed-Konrad model.

Task 2B deliberately retains `SW22/R34` because this phase represents the **stock baseline**. Task 2C will suppress R34 and add the trackball geometry.

All 20 switch position/rotation regressions passed at the validator's 1e-6 mm / 1e-6 degree tolerance.

## Other preserved PCB datums

The following stock references are also reconstructed and validated directly from the KiCad source:

- right encoder `SW18`;
- controller `U1`;
- TRRS `J1`;
- PCB mounting references `MH1..MH9`.

All position/rotation checks passed.

## Stock PCB Edge.Cuts

The stock PCB Edge.Cuts were reconstructed using Ergogen 4.2.1 `path` primitives rather than approximated polygons.

The source contains three closed chains:

| Chain | Source-derived segments | Result |
| --- | ---: | --- |
| Outer board perimeter | 66 | PASS |
| Internal cutout 1 | 8 | PASS |
| Internal cutout 2 | 6 | PASS |

Lines, arcs and cubic Bezier segments are compared directly against the stock KiCad source after coordinate transformation.

This gives Task 2C a precise stock board boundary on which to make the local breakout-notch modification.

## Stock switchplate perimeter

The switchplate outer contour was reconstructed from:

`klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.svg`

The outer contour contains **46 source-derived path segments** and is represented in Ergogen with lines and Bezier curves.

The regression passed against the checked-in SVG geometry after applying the previously source-validated KiCad-to-switchplate transform.

## Structural case/switchplate axes

The switchplate SVG contains eight structural M2 mounting axes. All eight are reconstructed in the same Task-2 canonical frame and numerically validated:

| Axis | X (mm) | Y (mm) |
| --- | ---: | ---: |
| case_mount_1 | 48.898826 | -39.659363 |
| case_mount_2 | 34.057332 | -40.666350 |
| case_mount_3 | 5.295366 | -40.620224 |
| case_mount_4 | -56.768833 | -40.650845 |
| case_mount_5 | -56.758358 | 38.777071 |
| case_mount_6 | 27.214179 | -8.336892 |
| case_mount_7 | 29.903255 | 25.310698 |
| case_mount_8 | 41.477996 | 26.081755 |

These axes are part of the preservation boundary for the minimal-change trackball design.

## Generated outputs

The Task 2B generation produces:

- canonical points YAML;
- exact stock board outline DXF/SVG;
- stock switchplate perimeter DXF/SVG;
- 20 fixed-Konrad switch-cutout references;
- nine stock PCB-hole references;
- eight structural case/switchplate axes;
- combined Task-2B preview;
- KiCad 8 stock-reference PCB scaffold.

Generated output remains disposable and ignored.

## Completion gate

| Gate | Result |
| --- | --- |
| Clean Ergogen generation succeeds | PASS |
| Two generation passes are deterministic | PASS |
| 20 fixed-Konrad key positions/rotations match stock | PASS |
| SW19 excluded from fixed Konrad | PASS |
| Encoder / MCU / TRRS match stock | PASS |
| MH1..MH9 references match stock | PASS |
| 66-segment outer PCB contour matches stock | PASS |
| 8-segment internal PCB contour matches stock | PASS |
| 6-segment internal PCB contour matches stock | PASS |
| 46-segment switchplate perimeter matches source SVG | PASS |
| Eight case/switchplate structural axes match source | PASS |
| Generated KiCad/DXF outputs exist | PASS |

## Architectural conclusion

Task 2B establishes the preserved-stock half of the canonical model.

The critical consequence is that Task 2C does **not** need to redesign KLOR geometry. It can be expressed as a bounded delta on top of a validated stock model:

1. suppress R34 / SW22;
2. add the 25 mm ball datum;
3. add Type-C housing envelope and mounting axes;
4. add the breakout/service corridor;
5. subtract the local PCB notch;
6. modify the local plate service geometry;
7. evaluate the PMW connector placement envelope.

Everything outside that delta should remain numerically unchanged.

## Next

Proceed to **Task 2C — Overlay the minimal trackball delta**.


## Preservation re-validation during Task 2C

Task 2C does not replace or mutate the Task-2B stock layer. The Task-2C CI workflow explicitly regenerates the complete model and re-runs `validate_task2b.py` before accepting any trackball delta.

Passing Task-2C preservation run:

- workflow: `KLOR Task 2C - trackball delta`
- run ID: `35804745592`
- head: `98c35cdf700785a2fd9d587f025f4ce8f7935e66`
- Task-2B preservation step: **PASS**

This confirms that the Task-2B stock geometry remains numerically unchanged while the Task-2C target geometry is layered on top.
