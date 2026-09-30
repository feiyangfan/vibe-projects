# Task 2E Result — Full 3D Mechanical Integration

> **SUPERSEDED / DO NOT USE AS CURRENT QUALIFICATION** — This result validated `keyball_trackball_case_25mm_type_c_right.stl`, which puts the physical connector on the wrong side for the intended right-hand assembly. Revision 5 reopens Task 2 with the mirrored housing. See `TASK2_REV5_HANDEDNESS.md`.

## Status

**PASS — COMPLETE.**

Task 2E proves the revision-4 trackball assembly in a common 3D frame using the real Type-C housing, a 25 mm sphere, the generated right PCB, stock Konrad switchplate and stock Konrad right case.

## Qualified geometry

Ball center:

`(15.5, -31.000147, 1.938015634)` mm

Stack:

- switchplate bottom: `z=0`;
- switchplate top: `z=1.5 mm`;
- Cherry MX plate-top to PCB-top: `5.0 mm`;
- PCB top: `z=-3.5 mm`;
- PCB bottom: `z=-5.1 mm`.

Ball exposure above plate top:

**12.938015634 mm**

Nearest retained key center:

- SW21: **34.196314 mm**.

## Mesh-level interference result

- 25 mm sphere vs PCB: **0 mm³**
- actual Type-C housing vs PCB: **0 mm³**
- sphere vs relieved switchplate: **0 mm³**
- housing vs relieved switchplate: `5.34e-7 mm³`
- sphere vs relieved right case: **0 mm³**
- housing vs relieved right case: `3.41e-7 mm³`

The non-zero values are numerical boolean residue below the `0.01 mm³` qualification tolerance.

All source meshes are watertight.

## Mechanical changes proven necessary

Task 2E disproved the revision-3 rigid PMW peninsula:

- revision-3 housing/PCB collision: approximately **158.111 mm³**;
- a Z-only workaround required approximately **24 mm** of ball exposure and was rejected.

Revision 4 therefore:

- moves the ball only `(-1,-3) mm` from revision 3;
- derives the PCB cavity from the actual housing/sphere clearance;
- preserves all 19 retained right keys and all nine PCB holes;
- retains the Kivipallur connector on the +X/right side of the ball;
- moves the keyboard-side 1x7 header to reclaimed SW22 PCB area;
- uses a short seven-conductor cable between the board and Kivipallur breakout.

## Switchplate and right case

The relieved switchplate is clearance-only around the housing.

The real housing relief removes the old plate support at the two native housing screw axes, so the right case gains a local downward pod and two bottom M2 mounting bosses.

Qualified pod:

- wall: 1.5 mm;
- floor: 1.5 mm;
- boss outer radius: 3.0 mm;
- both boss support checks: **100%**;
- downward extension below stock case: **5.461946 mm**.

This pod depth is a known physical/industrial-design tradeoff. It should be checked with a printed mock-up for desk contact and subjective comfort.

## Qualification evidence

Qualification head:

`52ea88ad36f9fe31962a599036b09c8a8fdb50d0`

Workflow:

- `KLOR Task 2E - 3D mechanical integration`
- run ID: `36376432664`
- conclusion: **success**

Artifact:

- `klor-task2e-3d-mechanical`
- artifact ID: `10950704578`
- SHA-256: `2d208bd05d018efb2099c31cfbfd0417193509a0986bcfd9cfa8c683f952fca9`

Contents:

- `task2e_konrad_switchplate_trackball.stl`
- `task2e_konrad_case_right_trackball.stl`
- `task2e_trackball_assembly.glb`
- `task2e_mechanical_result.json`

The same qualification head passed Tasks 2B, 2C revision 4, 2D revision 4, 3A, 3B, 3C and 3D revision 4.

## Conclusion

The revision-4 design is mechanically self-consistent in the declared source-aligned 3D frame: the actual housing and ball can coexist with the generated PCB and the generated plate/case modifications.

A physical print remains required for final subjective ergonomics and real-world desk-clearance validation.

## Next work — physical validation gate

**HOLD — documented only; do not start yet.**

Task 2E proves that the revision-4 parts are geometrically self-consistent in the declared common frame. The remaining risks are physical/ergonomic and cannot be closed by the current mesh-intersection gate alone.

The next work should be a **right-half mechanical mock-up**, before routing or committing to production fabrication.

### Mock-up contents

Print or fabricate enough of the right half to reproduce the real stack:

- relieved revision-4 Konrad switchplate;
- relieved revision-4 right case with trackball pod;
- actual Keyball 25 mm Type-C housing;
- 25 mm trackball;
- three 2 mm ceramic support balls;
- Kivipallur PMW3360 breakout / sensor / lens stack;
- representative MX switches and keycaps around the thumb/trackball region;
- representative M2 mounting hardware;
- representative seven-conductor cable between the Kivipallur breakout and board-side PMW header.

A full electrically functional PCB is not required for the first mechanical mock-up; a dimensionally correct PCB blank or printed substitute is sufficient if it reproduces PCB thickness, cavity, mounting holes and connector location.

### Physical checks

The mock-up must verify all of the following.

1. **Housing installation path**
   - the housing can actually be inserted and removed;
   - no hidden case/plate undercut blocks assembly even though the final-position meshes are collision-free;
   - screws and tools can reach both housing bosses.

2. **Ball retention and motion**
   - the 25 mm ball drops into the housing correctly;
   - all three ceramic bearings seat correctly;
   - the ball rotates freely through the useful range with no rubbing on the plate/case;
   - the ball cannot escape unintentionally during normal use.

3. **PMW3360 optical stack**
   - sensor/lens orientation matches the Type-C housing;
   - sensor-to-lens and lens-to-ball distances remain those intended by the housing;
   - the sensor can see the ball over the usable motion range;
   - connector/cable routing does not shift or preload the sensor assembly.

4. **Cable routing and strain**
   - the seven-conductor cable has a practical bend radius;
   - it does not rub the ball or bearings;
   - it does not interfere with switches, case screws or the pod;
   - there is usable strain relief at both breakout and board header.

5. **Thumb/key interference**
   - SW21 and adjacent keycaps can be pressed through full travel without contacting the thumb on the ball or the housing;
   - the thumb can reach and roll the ball without accidental key presses;
   - the approximately 12.94 mm exposed ball cap is usable in practice.

6. **Ergonomic reach**
   - confirm the qualified geometric distances with a real hand;
   - check neutral thumb posture, lateral reach and sustained ball use;
   - explicitly test whether the nearest retained-key distance (SW21 ≈ 34.20 mm) is comfortable;
   - test at least the intended primary user's hand; broader hand-size validation is desirable if the design is intended for others.

7. **Case pod / desk stance**
   - verify the 5.462 mm local downward pod does not become an unintended desk contact point;
   - check stock feet/tenting geometry;
   - confirm the keyboard does not rock;
   - if the pod touches the desk, decide whether to accept it, add/relocate feet, or redesign the pod.

8. **Fastener stack**
   - choose actual M2 screw lengths;
   - verify boss thread engagement or insert strategy;
   - verify screw heads do not collide with the ball/housing;
   - confirm repeated assembly is practical.

### Acceptance gate

Do not call the mechanical design production-ready until the physical mock-up passes the checks above.

If the mock-up passes with no geometry changes, revision 4 remains frozen and work can continue with **Task 3E cross-board electrical integration**, followed by **Task 4 routing**.

If the mock-up reveals a mechanical or ergonomic problem, reopen Task 2 before routing. Any change to ball XY/Z, cavity, housing orientation, case pod, PMW cable/header placement or retained thumb-key geometry must be treated as a new mechanical revision rather than a routing-time adjustment.

### Current stop point

The correct stop point is therefore:

- revision-4 CAD/mesh integration: **qualified**;
- physical installability in the modeled final position: **qualified by mesh**;
- physical assembly path, tracking stack, cable behavior, desk stance and subjective ergonomics: **not yet physically validated**;
- next action: **build and evaluate the mechanical mock-up**;
- implementation status: **do not start until explicitly resumed**.

