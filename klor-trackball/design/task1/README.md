# Task 1 — Mechanical reference assembly

Status: **in progress; not placement-locked**.

This directory is intentionally limited to Task 1. It must not contain production PCB routing, firmware changes, or final switchplate/case edits.

## Objective

Build one reproducible right-side reference assembly and use it to decide whether the current trackball placement can be locked.

The assembly must eventually contain:

- stock KLOR 1.4 right PCB geometry
- stock Konrad switchplate
- stock Konrad right case
- Keyball 25 mm Trackball Case Type C
- 25 mm ball
- Kivipallur PMW3360 breakout
- R32/R33 switch and keycap envelopes
- right encoder envelope
- MCU/TRRS keepouts

The current placement remains the baseline. It should move only if the complete assembly exposes a concrete collision or assembly/service constraint.

## Current source state

### Type-C housing files are checked in directly

The unarchived Thingiverse source package is now stored at:

`../../Keyball 25mm Trackball Case Type C - 6719828/`

Task 1 uses these files directly:

- `files/keyball_trackball_case_25mm_type_c.stp` — primary CAD source
- `files/keyball_trackball_case_25mm_type_c_left.stl` — source-package reference
- `files/keyball_trackball_case_25mm_type_c_right.stl` — source-package reference

The recorded SHA-256 values are:

- STEP: `79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c`
- left STL: `5bcd5f2ec9cf4f151f15423a27f68a44c96efbc45ad7ce103242b5b66511ab58`
- right STL: `9ff67b5fe3acee937a14b84994b586b2993a2e0222d826da7d0275e4c68c4565`

The original ZIP remains at the project root as provenance/reference, but Task 1 no longer depends on archive extraction.

`preflight_reference_assembly.py` verifies the checked-in STEP and STL files directly. The ZIP check is supplementary and can be skipped with `--skip-archive-check`.

Do not substitute a redraw or approximate envelope for the checked-in STEP.

### The stock right case is mesh-only

The regular Konrad right case is available as:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

That is sufficient for collision/reference work in Task 1, but not a clean editable source for Task 5.

### Cross-model coordinate alignment is still unresolved

The trackball datums are expressed in the native KLOR PCB/Gerber XY frame. The Konrad switchplate STEP and right-case STL do not yet have a documented transform back to that PCB frame.

Task 1 must establish and record those transforms from geometry. They must not be guessed from screenshots or bounding boxes.

## Source-of-truth manifest

`reference_assembly_manifest.yaml` records:

- current placement datums
- direct housing STEP/STL paths and expected hashes
- stock source files
- unresolved transforms
- the Task 1 completion gate

A completion-gate field must remain `false` until it has been checked against the assembled source geometry.

## Reference assembly workflow

1. Run the preflight. It verifies the stock sources and the checked-in Type-C STEP/STLs directly.
2. Export the stock KLOR PCB to STEP from the existing KiCad board without editing it.
3. Align the stock Konrad switchplate to the PCB using common physical features (switch centers and/or mounting features), then record the rigid transform.
4. Align the stock right-case STL to the switchplate/PCB assembly using matching seating and mounting geometry, then record the rigid transform.
5. Place the verified Type-C STEP using the recorded ball-centred transform and align its mounting plane to the switchplate interface.
6. Add the real Kivipallur breakout geometry and verify its orientation and insertion/service path.
7. Add R32/R33, encoder, MCU and TRRS collision envelopes from source geometry or verified component dimensions.
8. Run the complete collision/access audit and write the results into the manifest.

Run preflight from `klor-trackball/`:

```bash
python3 design/task1/preflight_reference_assembly.py
```

To omit the supplementary ZIP cross-check:

```bash
python3 design/task1/preflight_reference_assembly.py --skip-archive-check
```

To also export the unmodified stock PCB as a board-only STEP when `kicad-cli` is installed:

```bash
python3 design/task1/preflight_reference_assembly.py --export-pcb-step
```

## Required outputs before Task 1 can close

- a reproducible reference assembly file or script
- recorded PCB → switchplate and PCB → case transforms
- verified direct Type-C STEP/STL hashes
- collision results for all retained components/keepouts
- verified ball exposure and housing mounting-plane relationship
- verified breakout insertion/service path
- `placement_locked: true` only after every completion-gate item passes

If the placement changes, update `reference_assembly_manifest.yaml`, `../konrad_trackball_geometry.yaml`, and `../../docs/KONRAD_TRACKBALL_HANDOFF.md` together.
