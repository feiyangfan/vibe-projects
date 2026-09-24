# Task 2C Result — Connector-Right Trackball Delta

## Status

**PASS — Task 2C revision 2 is complete.**

Revision 2 supersedes the original left-side breakout orientation. The canonical trackball assembly now matches the handedness of the checked-in KLORBall-35 right PCB: the Kivipallur/keyboard connector is on the **right / positive canonical X side of the ball**.

## Why the ball center moved

A direct 180 degree flip around the previous ball center `(22.261644, -28.000147)` puts the conservative Type-C housing envelope into retained SW16.

The minimum-change correction is an inward X shift only:

```text
prior ball center   = (22.261644, -28.000147)
revision-2 center   = (16.500000, -28.000147)
delta               = (-5.761644, 0)
```

This preserves:

- all 19 retained right MX positions;
- R32 / SW20 and R33 / SW21;
- the stock right encoder;
- MCU and TRRS datums;
- all nine stock PCB mounting holes;
- all stock case/switchplate structural axes.

The conservative housing-to-key gate passes with SW16 as the limiting retained key at approximately **2.580294 mm**.

The connector-right 2 x 22 service notch also clears stock MH8 by approximately **3.354275 mm edge-to-drill**.

## Canonical revision-2 relationships

```text
ball_center
    = (16.5, -28.000147)

housing_center
    = ball_center + (9.165901, 0.000812)

housing_screw_midpoint
    = ball_center + (6.212, 0)

housing_screw_1 / 2
    = midpoint + (0, +/-7.98)

breakout_center
    = ball_center + (19.212, 0)

pmw_header_center
    = breakout_center + (-4.613622, 0)
```

Therefore:

```text
breakout_center   = (35.712, -28.000147)
pmw_header_center = (31.098378, -28.000147)
```

Both remain to the right of the ball.

## PMW connector handedness

The checked-in KLORBall-35 right PCB was audited directly.

Its keyboard-side J2 order is:

1. CS
2. MISO
3. MOSI
4. SCK
5. NC / MOTION
6. 3V3
7. GND

In the canonical frame, **pin 1 / CS is at positive Y** and **pin 7 / GND is at negative Y**.

Revision 2 adopts that physical direction while preserving the verified Kivipallur mating rule:

`breakout pin N -> keyboard pin 8-N`.

## PCB delta

The target right PCB remains:

```text
stock_board
+ pmw_support_tongue
- breakout_service_slot
= trackball_board
```

The connector-right header now sits over the sloped lower stock edge, so the support tongue is re-derived rather than mirrored blindly.

Frozen tongue:

```text
center_from_breakout = (-3.9444785, -0.0894995)
size                 = 5.888957 x 18.825007 mm
```

At the header center, the body extends approximately **18.092963 mm** beyond the stock lower edge. The tongue joins the stock edge at its inner X side and terminates at the negative-X edge of the service notch.

The 2 x 22 service opening is now a separate connector-right corridor; the removed SW22/R34 aperture remains preserved as already-open switchplate material rather than being treated as a merged corridor.

## Qualification

Qualification head:

`53db19fc1d0049b4bcc4f311a69ae30ba4713313`

Passing workflow:

- `KLOR Task 2C - trackball delta`
- run ID: `35948524860`
- conclusion: **success**

Artifact:

- `klor-task2c-trackball-geometry`
- artifact ID: `10787711234`
- SHA-256: `8486ccbcb33b3323aa8ef57ea031fdc385d98d102f68f1591fa900ea35afa52f`

The workflow also re-ran and passed the complete Task-2B stock-preservation gate.

## Conclusion

Task 2C revision 2 preserves the fixed Konrad controls and stock mounting system while changing only the trackball placement/orientation and the local connector-support geometry required to put the PMW connector on the right side of the ball.
