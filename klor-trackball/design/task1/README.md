# Task 1 — Mechanical reference assembly

Status: **complete — placement locked**.

Task 1 establishes the mechanical reference frame and proves the current Type-C trackball placement against the checked-in KLOR/Konrad geometry. It intentionally does **not** modify the production PCB, firmware, switchplate, or case.

The detailed result is in [`TASK1_RESULT.md`](TASK1_RESULT.md). The machine-readable source of truth is [`reference_assembly_manifest.yaml`](reference_assembly_manifest.yaml).

## Locked result

The original fabrication-frame placement remains unchanged:

| Datum | X | Y |
| --- | ---: | ---: |
| Ball center | 162.323 | -134.748 |
| Housing screw midpoint | 156.111 | -134.748 |
| Housing screw 1 | 156.111 | -126.768 |
| Housing screw 2 | 156.111 | -142.728 |
| Breakout-slot center | 143.111 | -134.748 |

These values are explicitly **Gerber/Excellon fabrication coordinates**. The audit solved the fabrication↔KiCad transform from all 21 MX drill-center pairs and confirmed it is effectively an X-preserving, Y-reflecting transform.

## What was verified

The automated geometry audit verifies:

- checked-in Type-C STEP/right-STL/left-STL hashes and ZIP provenance;
- KiCad PCB ↔ Gerber/Excellon frame;
- KiCad PCB ↔ native Konrad switchplate frame;
- native Konrad switchplate ↔ native right-case frame from eight structural M2 axes;
- stock case support plane + documented 7 mm standoff + 1.5 mm switchplate stack-up;
- Type-C mounting plane and ball exposure;
- nearest retained switch/keycap clearances;
- right encoder, MCU, and TRRS clearances;
- all eight structural fastener axes using the actual housing mesh and conservative M2 fastener envelopes;
- Kivipallur breakout orientation and insertion/service corridor.

The authoritative completion gate passes with `placement_locked: true`.

## Important downstream finding

The unmodified stock right-case shell intersects the placed Type-C housing. This is **not** a reason to move the trackball:

- all eight structural case/switchplate mounting axes remain clear;
- retained switches, encoder, MCU, and TRRS remain clear;
- the interference is local shell material in the intended trackball modification region.

Task 5 must therefore provide local case-shell relief around the locked housing placement while preserving all eight structural mounting axes. Task 4 will likewise add the required local switchplate relief and Type-C mounting features.

## Source geometry

Type-C source package:

`../../Keyball 25mm Trackball Case Type C - 6719828/`

Primary files:

- `files/keyball_trackball_case_25mm_type_c.stp`
- `files/keyball_trackball_case_25mm_type_c_left.stl`
- `files/keyball_trackball_case_25mm_type_c_right.stl`

Stock/reference geometry:

- PCB: `../../klor1.4/PCB/klor1_4/klor1_4.kicad_pcb`
- NPTH drill/frame reference: `../../klor1.4/PCB/klor1_4/gerbers/klor1_4-NPTH.drl`
- switchplate: `../../klor1.4/case/3DP/konrad/switchplate/KLOR_konrad_3DP_switchplate.step`
- right case: `../../klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`
- breakout: `../../klorball35/kicad/Kivipallur_PMW3360_breakout/Kivipallur_PMW3360_breakout.kicad_pcb`

## Reproducing the audit

From `klor-trackball/`:

```bash
python3 design/task1/preflight_reference_assembly.py
```

The full audit runs in GitHub Actions through:

`.github/workflows/klor-task1-mechanical-audit.yml`

It generates machine-readable evidence for the frame solves, stack-up, collision checks, structural-fastener checks, and final completion gate.

## Gate for later tasks

Tasks 2–8 must use the locked fabrication datums in the manifest. Do not move the trackball merely to avoid the documented stock-case shell relief.

If the placement is ever changed, rerun Task 1 and update together:

- `reference_assembly_manifest.yaml`
- `../konrad_trackball_geometry.yaml`
- `../../docs/KONRAD_TRACKBALL_HANDOFF.md`
