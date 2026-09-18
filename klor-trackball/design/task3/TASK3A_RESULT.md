# Task 3A result — KiCad derivative project

Status: **COMPLETE**.

Task 3A creates the editable KiCad baseline for the KLOR Konrad PMW3360 right-hand PCB derivative. No Task 2 electrical modifications are made yet.

## Derivative location

```text
klor-trackball/PCB/konrad_trackball/
```

Project basename:

```text
konrad_trackball
```

The project remains **schematic-driven**. Task 3B will implement the frozen Task 2 electrical contract in the derivative schematic before destructive PCB/routing work begins.

## Files carried forward

The derivative contains:

- `konrad_trackball.kicad_pro`
- `konrad_trackball.kicad_sch`
- `konrad_trackball.kicad_pcb`
- `konrad_trackball.kicad_dru`
- `konrad_trackball.round-tracks-config`
- `KLORlib.kicad_sym`
- `KLOR.pretty/`
- `fp-lib-table`
- `sym-lib-table`
- derivative-specific `README.md`

The stock `gerbers/` directory is intentionally **not** copied.

## Baseline equivalence

At Task 3A completion:

- derivative PCB is byte-identical to stock `klor1_4.kicad_pcb`;
- derivative schematic is byte-identical to stock `klor1_4.kicad_sch`;
- design rules are byte-identical;
- round-track configuration is byte-identical;
- local symbol library is byte-identical;
- complete local footprint-library tree is identical;
- footprint/symbol library tables are byte-identical and remain project-local through `${KIPRJMOD}`;
- the stock source Git objects are locked against the known Task 3A baseline.

The only intentional content difference in the KiCad project file is:

```text
meta.filename:
  klor1_4.kicad_pro
  →
  konrad_trackball.kicad_pro
```

No electrical or PCB design change is authorized by this rename.

## Why fabrication output is excluded

The stock KLOR Gerbers describe the unmodified board. Copying them into the derivative would create stale fabrication artifacts that could be mistaken for outputs from the trackball board.

Fabrication files must be regenerated from the completed derivative during the later fabrication task.

## Stock source remains immutable

Task 3 implementation occurs under:

```text
klor-trackball/PCB/konrad_trackball/
```

The stock project remains under:

```text
klor-trackball/klor1.4/PCB/klor1_4/
```

and is reference-only.

## Task 3A gate

Task 3A passes when the audit proves:

- known stock project Git objects are unchanged;
- all required derivative source files exist;
- PCB and schematic are exact baseline copies;
- local libraries and design rules are exact baseline copies;
- project-local library resolution is preserved;
- project metadata identifies the derivative basename;
- no stock Gerbers are inherited;
- SW22/D22 still exist, proving Task 3B electrical work has not been mixed into 3A.

**Task 3A: COMPLETE.**

Next: **Task 3B — implement the schematic contract.**
