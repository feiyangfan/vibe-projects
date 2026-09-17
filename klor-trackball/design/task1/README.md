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

## Current blockers found from `main`

### 1. Type-C STEP is referenced but not stored in the repository

The handoff records the exact Type-C STEP hash:

`79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c`

The source file itself is absent from `klor-trackball/`. Task 1 cannot claim a source-geometry collision pass until that exact file is available and its hash is verified.

Do not substitute a similarly named STL or redraw the housing from the recorded bounding box.

### 2. The stock right case is mesh-only here

The regular Konrad right case is available as:

`klor1.4/case/3DP/konrad/regular/KLOR_konrad_case_R.stl`

That is sufficient for collision/reference work in Task 1, but not a clean editable source for Task 5.

### 3. Cross-model coordinate alignment is not documented

The trackball datums are expressed in the native KLOR PCB/Gerber XY frame. The Konrad switchplate STEP and right-case STL do not have a documented transform back to that PCB frame.

Task 1 must establish and record those transforms from geometry. They must not be guessed from screenshots or bounding boxes.

## Source-of-truth manifest

`reference_assembly_manifest.yaml` records:

- current placement datums
- expected Type-C source hash
- stock source files
- unresolved transforms
- the Task 1 completion gate

A completion-gate field must remain `false` until it has been checked against the assembled source geometry.

## Reference assembly workflow

1. Export the stock KLOR PCB to STEP from the existing KiCad board without editing it.
2. Align the stock Konrad switchplate to the PCB using common physical features (switch centers and/or mounting features), then record the rigid transform.
3. Align the stock right-case STL to the switchplate/PCB assembly using matching seating and mounting geometry, then record the rigid transform.
4. Obtain the exact Type-C STEP identified by the recorded SHA-256 and verify the hash before use.
5. Place the Type-C housing using the recorded ball-centred transform and align its mounting plane to the switchplate interface.
6. Add the real Kivipallur breakout geometry and verify its orientation and insertion/service path.
7. Add R32/R33, encoder, MCU and TRRS collision envelopes from source geometry or verified component dimensions.
8. Run the complete collision/access audit and write the results into the manifest.

## Required outputs before Task 1 can close

- a reproducible reference assembly file or script
- recorded PCB → switchplate and PCB → case transforms
- verified Type-C source hash
- collision results for all retained components/keepouts
- verified ball exposure and housing mounting-plane relationship
- verified breakout insertion/service path
- `placement_locked: true` only after every completion-gate item passes

If the placement changes, update `reference_assembly_manifest.yaml`, `../konrad_trackball_geometry.yaml`, and `../../docs/KONRAD_TRACKBALL_HANDOFF.md` together.
