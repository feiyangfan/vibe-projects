# Ergogen Workspace

This directory is the active geometric workspace for the KLOR trackball migration.

## Task 0 prototype

Task 0 proves the generation architecture before the complete keyboard is modeled.

`config.yaml` currently contains a **sparse regression slice**:

- stock KLOR switch centers SW13, SW14, SW15, SW21 and SW22;
- stock U1, TRRS/ J1 and right encoder reference points;
- stock right-side mounting references MH5, MH7 and MH8;
- the historical validated trackball center and breakout center;
- an Ergogen-generated prototype board and plate;
- one built-in Ergogen MX footprint and one RGB footprint on SW13.

SW13 is the temporary Task 0 origin. Stock KiCad +Y is reflected into a conventional Cartesian +Y-up Ergogen frame. Task 2 will replace these independent anchors with the full parametric Konrad layout.

## Generation

From this directory:

```bash
npx --yes ergogen@4.2.1 . --output generated --clean --svg
python -m pip install PyYAML==6.0.2
python scripts/validate_task0.py --generated generated
```

The validator does **not** trust copied coordinates. It parses the checked-in stock KLOR KiCad PCB, derives the Task 0 reference frame from SW13, and compares the generated Ergogen points numerically. Trackball/breakout points are compared with the historical reference datums in `reference-baseline.yaml`.

CI generates the project twice and diffs both output trees before running the geometry regression. Generated output remains disposable and ignored.

## Task 0 gate

Task 0 passes when CI proves all of the following:

1. Ergogen 4.2.1 can generate this repository directly from `config.yaml`.
2. two clean generation passes are byte-for-byte equivalent;
3. selected stock switch/component/mount points match numerically;
4. trackball and breakout reference points match the prior validated datums;
5. a KiCad 8 PCB is emitted with MX and RGB prototype footprints/nets;
6. a plate DXF and visual reference preview are emitted.

This gate proves the workflow. It does **not** claim the prototype outline or built-in MX/RGB footprints are final production geometry.

## Reference policy

`reference-baseline.yaml` is regression evidence, not the new design authority. The complete retired implementation remains available at Git commit `432ea630584c22dff2e9f5a596138dcc7602013f`.
