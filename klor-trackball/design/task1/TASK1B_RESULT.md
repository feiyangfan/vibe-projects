# Task 1B result — common coordinate frame

Status: **complete**.

Task 1A is complete, so Task 1B is allowed to consume the checked-in mechanical source set. Task 1B establishes reproducible XY transforms between the stock KLOR PCB, fabrication frame, Konrad switchplate, and right-case model.

No transform below is based on screenshots, bounding boxes, or a single picked point. Each fitted transform uses multiple physical features from the source geometry.

## KiCad PCB → Gerber/Excellon fabrication frame

Solved from all 21 MX centers in the NPTH drill data:

```text
R = [[ 1.000000000,  0.000000342],
     [ 0.000000342, -1.000000000]]
t = [-0.000089, -0.000052] mm
```

- matched features: **21 / 21**
- RMS residual: **0.000181078 mm**

The fabrication frame is therefore, to the accuracy required here, the KiCad frame with X preserved and Y reflected.

## KiCad PCB → native Konrad switchplate frame

Solved from the 18 Konrad MX openings:

```text
R = [[ 0.999999991,  0.000131877],
     [ 0.000131877, -0.999999991]]
t = [-80.655587, 153.995244] mm
```

- matched features: **18 / 18**
- RMS residual: **0.020018840 mm**

## Native switchplate → native right-case frame

Solved from the eight structural M2 mounting axes:

```text
R = [[ 0.999999999,  0.000033962],
     [-0.000033962,  0.999999999]]
t = [80.582795, 55.951799] mm
```

- matched features: **8 / 8**
- RMS residual: **0.006063240 mm**

## Composed KiCad PCB → native right-case frame

For downstream code that starts directly from KiCad coordinates, compose the two verified transforms:

```text
R_case_from_kicad = R_case_from_plate @ R_plate_from_kicad

t_case_from_kicad =
    R_case_from_plate @ t_plate_from_kicad
    + t_case_from_plate
```

Result:

```text
R = [[ 0.999999994,  0.000097915],
     [ 0.000097915, -0.999999994]]
t = [-0.067561933, 209.949782] mm
```

This transform is **composed**, not independently direct-fitted. Therefore it must not be assigned a fabricated direct-fit RMS value. A conservative propagated residual bound is:

```text
0.020018840 + 0.006063240 = 0.026082080 mm
```

So the documented conservative bound is **≤ 0.026082080 mm**.

## Gate result

Task 1B requires that the PCB, switchplate, and right case can be overlaid reproducibly in one common mechanical frame using multi-feature evidence with quantified error.

That condition is satisfied:

- PCB ↔ fabrication frame verified from 21 features;
- PCB ↔ switchplate verified from 18 features;
- switchplate ↔ case verified from 8 structural axes;
- direct PCB → case composition explicitly recorded;
- all residuals are quantified and retained in the machine-readable manifest.

**Task 1B: COMPLETE.**

The canonical numeric values are also recorded under `verified_transforms` in [`reference_assembly_manifest.yaml`](reference_assembly_manifest.yaml).
