# Task 1 Result — Product Requirements Freeze

## Status

**PASS — Task 1 is complete.**

The Rev-1 product contract is frozen in `../REQUIREMENTS.md`.

Task 1 was intentionally a requirements audit, not an implementation task. Its purpose was to separate the desired keyboard from legacy KLOR features and from constraints created by the retired KiCad-patching workflow.

## Sources audited

Primary repository evidence:

- `klor1.4/README.md` — stock KLOR capabilities, layouts, PCB/case scope;
- `klor1.4/FABNOTES.md` — MX hardware, RP2040/wired guidance, power-switch implications, fabrication constraints;
- `klor1.4/FIRMWARE.md` — QMK/ZMK split behavior and handedness guidance;
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/keyboard.json` — Konrad matrix/layout, encoder and stock feature inventory;
- `klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor/config.h` — stock GPIO ownership and optional OLED/audio/haptic/PAW3204 conflicts;
- `klorball35/README.md` and `klorball35/config.yml` — PMW3360/Kivipallur/Ergogen reference architecture;
- `klorball35/kicad/klorball35_right/klorball35_right.kicad_pcb` — 1x7 trackball connector implementation;
- `klorball35/kicad/Kivipallur_PMW3360_breakout/` — breakout reference and signal ordering;
- `Keyball 25mm Trackball Case Type C - 6719828/` — 25 mm housing reference and licensing;
- historical pre-migration `design/konrad_trackball_geometry.yaml` at commit `432ea630584c22dff2e9f5a596138dcc7602013f` — previously validated mechanical/electrical evidence.

External compatibility was also checked against current QMK documentation for:

- PMW3360 pointing-device support;
- split pointing;
- RP2040 split keyboards;
- half-duplex serial.

## Product decisions

The audit freezes Rev 1 as:

- KLOR 1.4 MX;
- fixed Konrad;
- separate left/right PCBs;
- 20 left keys fixed;
- right-thumb R32/R33/R34 occupancy intentionally delegated to Task 2;
- historical 39-key / R34-only removal retained as a comparison baseline, not a requirement;
- left encoder retained;
- right encoder intentionally delegated to Task 2 and may be retained, relocated, or removed;
- 25 mm PMW3360 on the right;
- Kivipallur breakout;
- Type-C housing;
- 1x7 2.54 mm breakout connector;
- full-height MX hotswap;
- per-key SK6812 Mini-E RGB;
- wired RP2040/QMK;
- TRRS half-duplex split;
- regular wired Konrad mechanical family.

## Removed complexity

Rev 1 intentionally drops:

- universal/reversible PCB architecture;
- alternate KLOR layouts and break-away sections;
- OLED;
- haptic;
- audio;
- stock PAW3204;
- battery/power-switch hardware;
- wireless/ZMK requirement;
- tenting-puck compatibility requirement;
- full-duplex split transport.

These are not “DNP for now” features. They are outside the Rev-1 hardware contract.

## Why this satisfies the gate

Task 2 can now model geometry without waiting on decisions about:

- layout variant;
- trackball family;
- housing family;
- case family;
- reversible-vs-separate-PCB architecture;
- structural interfaces;
- connector class.

Task 3 can implement the electrical board **after Task 2 locks the right-thumb architecture**. It will not need to revisit decisions about:

- controller class;
- wired vs wireless;
- QMK vs ZMK primary target;
- trackball signal set;
- obsolete optional peripherals.

Task 4 can design the routing pipeline around a fixed hardware feature set.

There are no unresolved product-level decisions blocking **Task 2**. Task 2 deliberately owns one bounded product decision: the final right-thumb key set / total key count / right-encoder retention. That geometry decision must be frozen before Task 3.

## Right-thumb decision deliberately deferred to Task 2

The original Task-1 draft over-froze the retired implementation.

The recheck confirmed:

- stock mapping: R32 = SW20, R33 = SW21, R34 = SW22;
- the historical derivative removed R34/SW22/D22;
- its validated assembly reported only about **3.44 mm** conservative XY gap to retained SW21/R33 and about **2.65 mm** to SW15;
- the right encoder had about **27.77 mm** conservative XY gap in that historical placement.

Therefore R34-only is mechanically feasible, but it is not automatically the best ergonomic architecture, and the right encoder was not a necessary constraint in the old placement.

Task 2 must compare right-thumb/encoder alternatives and lock the final architecture before electrical generation.

## Implementation details intentionally deferred

The following remain valid downstream engineering decisions rather than product ambiguity:

- exact RP2040 Pro Micro-compatible controller model;
- final GPIO assignment after Task-3 validation;
- exact trackball absolute coordinates, to be re-derived parametrically in Task 2;
- final retained subset of R32/R33/R34 and resulting total key count;
- right encoder retained / relocated / removed;
- route topology;
- zones;
- detailed right-case relief shape;
- CPI/orientation/scroll tuning;
- Vial support.

## Handoff

Proceed to **Task 2 — Reconstruct the complete KLOR/Konrad geometry in Ergogen**.
