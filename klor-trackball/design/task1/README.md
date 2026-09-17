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

### 1. Type-C housing archive is now stored in the repository

The archive is available at:

`../../Keyball 25mm Trackball Case Type C - 6719828.zip`

The handoff records these expected hashes:

- archive SHA-256: `ad2ee79388c01fcb775ee08e35761d14b27fbd53ecffabfbdc45add77830e206`
- embedded STEP SHA-256: `79c3fdc445d6b4ecf63afdcc60d87a7ab3635902f155187c6687e3561d1ed57c`
- embedded STEP member: `files/keyball_trackball_case_25mm_type_c.stp`

`preflight_reference_assembly.py` now checks the repository archive automatically, verifies both hashes, and verifies that the expected STEP member is present before Task 1 uses the housing geometry.

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
- repository housing archive path
- expected archive and embedded STEP hashes
- stock source files
- unresolved transforms
- the Task 1 completion gate

A completion-gate field must remain `false` until it has been checked against the assembled source geometry.

## Reference assembly workflow

1. Run the preflight. It verifies stock sources, the repository housing archive, and the embedded Type-C STEP.
2. Export the stock KLOR PCB to STEP from the existing KiCad board without editing it.
3. Align the stock Konrad switchplate to the PCB using common physical features (switch centers and/or mounting features), then record the rigid transform.
4. Align the stock right-case STL to the switchplate/PCB assembly using matching seating and mounting geometry, then record the rigid transform.
5. Extract/use the verified Type-C STEP and place it using the recorded ball-centred transform; align its mounting plane to the switchplate interface.
6. Add the real Kivipallur breakout geometry and verify its orientation and insertion/service path.
7. Add R32/R33, encoder, MCU and TRRS collision envelopes from source geometry or verified component dimensions.
8. Run the complete collision/access audit and write the results into the manifest.

Run preflight from the project root:

```bash
python3 design/task1/preflight_reference_assembly.py
```

To also export the unmodified stock PCB as a board-only STEP when `kicad-cli` is installed:

```bash
python3 design/task1/preflight_reference_assembly.py --export-pcb-step
```

## Required outputs before Task 1 can close

- a reproducible reference assembly file or script
- recorded PCB → switchplate and PCB → case transforms
- verified repository archive and embedded Type-C STEP hashes
- collision results for all retained components/keepouts
- verified ball exposure and housing mounting-plane relationship
- verified breakout insertion/service path
- `placement_locked: true` only after every completion-gate item passes

If the placement changes, update `reference_assembly_manifest.yaml`, `../konrad_trackball_geometry.yaml`, and `../../docs/KONRAD_TRACKBALL_HANDOFF.md` together.
