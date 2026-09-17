# Task 1 — Mechanical reference assembly

Status: **complete — placement locked**.

Task 1 establishes the mechanical reference frame and proves the current Type-C trackball placement against the checked-in KLOR/Konrad geometry. It intentionally does **not** modify the production PCB, firmware, switchplate, or case.

The detailed final result is in [`TASK1_RESULT.md`](TASK1_RESULT.md). The machine-readable source of truth is [`reference_assembly_manifest.yaml`](reference_assembly_manifest.yaml).

## Subtask decomposition

Task 1 is now decomposed into explicit gates:

`1A → 1B → 1C → 1D → 1E → 1F → 1G`

The original mechanical audit was completed before this decomposition was introduced. Therefore the split is a traceability/refinement of an already successful audit, not a claim that the later checks have never been performed.

| Subtask | Purpose | Status | Primary evidence |
| --- | --- | --- | --- |
| 1A | Lock source geometry | **complete** | preflight/hash verification |
| 1B | Establish common coordinate frame | **complete** | [`TASK1B_RESULT.md`](TASK1B_RESULT.md) + transform diagnostics |
| 1C | Place housing and ball in XYZ | **complete** | stack-up + source-model placement in manifest |
| 1D | Place breakout and verify service path | **complete** | breakout audit/service-path evidence |
| 1E | Add retained-component keepouts | **complete** | retained switch/encoder/MCU/TRRS + mount evidence |
| 1F | Collision and clearance audit | **complete** | `TASK1_RESULT.md` + final audit |
| 1G | Freeze or revise placement | **complete** | `placement_locked: true` |

For future geometry changes, rerun these subtasks in order rather than treating Task 1 as a single opaque check.

## Task 1A — Lock source geometry

**Gate: complete.**

The audit identifies and verifies the exact mechanical inputs:

- Type-C STEP
- Type-C left STL
- Type-C right STL
- original Thingiverse ZIP provenance
- stock KLOR PCB
- NPTH drill/fabrication-frame reference
- Konrad switchplate
- stock right-case STL
- Kivipallur breakout PCB source

Type-C source package:

`../../Keyball 25mm Trackball Case Type C - 6719828/`

Verified source hashes:

| File | SHA-256 |
| --- | --- |
| Type-C STEP | `79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c` |
| left STL | `5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58` |
| right STL | `9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565` |
| ZIP provenance | `ad2ee79388c01fcb775ee08e35761d14b27fbd53ecffabfbdc45add77830e206` |

The successful mechanical-audit run verified these values from the checked-in bytes. Task 1A therefore passes and Task 1B is permitted to consume these files.

## Task 1B — Establish the common coordinate frame

**Gate: complete.**

Task 1B uses multiple physical features for each solve. No transform is inferred from screenshots, bounding boxes, or a single point.

### KiCad PCB → Gerber/Excellon fabrication frame

Solved from all 21 MX centers in the NPTH drill data:

```text
R = [[ 1.000000000,  0.000000342],
     [ 0.000000342, -1.000000000]]
t = [-0.000089, -0.000052] mm
```

- matched features: **21**
- RMS residual: **0.000181078 mm**

Practically, the fabrication frame preserves X and reflects Y.

### KiCad PCB → native Konrad switchplate frame

Solved from 18 Konrad MX openings:

```text
R = [[ 0.999999991,  0.000131877],
     [ 0.000131877, -0.999999991]]
t = [-80.655587, 153.995244] mm
```

- matched features: **18**
- RMS residual: **0.020018840 mm**

### Native switchplate → native right-case frame

Solved from all eight structural M2 mounting axes:

```text
R = [[ 0.999999999,  0.000033962],
     [-0.000033962,  0.999999999]]
t = [80.582795, 55.951799] mm
```

- matched features: **8**
- RMS residual: **0.006063240 mm**

### Composed KiCad PCB → native right-case frame

Composing the two independently verified transforms above gives:

```text
R = [[ 0.999999994,  0.000097915],
     [ 0.000097915, -0.999999994]]
t = [-0.067561933, 209.949782] mm
```

This is a **composed transform**, not a separate direct fit. A conservative propagated residual bound is the sum of the two constituent RMS residuals:

`≤ 0.026082080 mm`

The transform is recorded in the manifest and separately summarized in [`TASK1B_RESULT.md`](TASK1B_RESULT.md).

**1B completion condition is satisfied:** PCB, switchplate, and right case can be placed reproducibly into one common mechanical frame with quantified alignment error.

## Task 1C — Place the housing and ball

**Gate: complete.**

The locked fabrication-frame placement is:

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | 162.323 | -134.748 |
| Housing screw midpoint | 156.111 | -134.748 |
| Housing screw 1 | 156.111 | -126.768 |
| Housing screw 2 | 156.111 | -142.728 |
| Breakout-slot center | 143.111 | -134.748 |

The stock stack-up resolves the switchplate top / Type-C mounting plane to case `Z = 7.7 mm`. The 25 mm ball top is at case `Z = 38.2 mm`; the housing rim is approximately `Z = 38.9 mm`.

## Task 1D — Place breakout and verify service path

**Gate: complete.**

The Kivipallur Edge.Cuts are 22 × 25 mm and the Klorball reference pass-through is 2 × 22 mm. Orientation and inward service direction were verified, with approximately 8.000 mm minimum retained-keycap corridor clearance.

## Task 1E — Retained-component keepouts

**Gate: complete.**

The audit includes retained switch/keycap envelopes, encoder, MCU, TRRS, and all eight structural mounting axes with conservative M2 fastener envelopes.

## Task 1F — Collision and clearance audit

**Gate: complete.**

Key results:

- nearest retained switch/keycap gap: `SW15` **2.654 mm**
- next retained switch/keycap gap: `SW21` **3.444 mm**
- right encoder `SW18`: **27.772 mm**
- MCU `U1`: **40.321 mm**
- TRRS `J1`: **46.460 mm**
- structural fastener collisions: **0 / 8**
- structural boss collisions: **0 / 8**

The unmodified stock right-case shell intersects the housing locally. That is an expected downstream case-relief requirement rather than a placement failure because the verified structural mounts and retained components remain clear.

## Task 1G — Freeze or revise placement

**Gate: complete.**

The original candidate placement did not need to move. The authoritative result is:

**`placement_locked: true`**

Do not move the trackball merely to avoid the documented local stock-case shell relief.

If the placement is ever changed, rerun Task 1A–1G and update together:

- `reference_assembly_manifest.yaml`
- `../konrad_trackball_geometry.yaml`
- `../../docs/KONRAD_TRACKBALL_HANDOFF.md`

## Reproducing the audit

From `klor-trackball/`:

```bash
python3 design/task1/preflight_reference_assembly.py
```

The full audit runs in GitHub Actions through:

`.github/workflows/klor-task1-mechanical-audit.yml`

It generates machine-readable evidence for the frame solves, stack-up, collision checks, structural-fastener checks, and final completion gate.

## Gate for later tasks

Tasks 2–8 must use the locked fabrication datums in the manifest. Task 1 locks the reference mechanical placement; it does not by itself make the complete keyboard fabrication-ready.