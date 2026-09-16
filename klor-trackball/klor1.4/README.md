# Welcome to my take on the great KLOR Split Keyboard Project
Here you'll find an up do date version of KLOR PCB and firmware files for Rev 1.4 for full height Cherry switches and a Rev 1.4 LP KS33 version for low profile KS33 Gateron switches.

If you intend to build a KLOR keyboard from this repo please take the time to read the different sections below.

![KLOR](/docs/images/Klor_1.4_picture6.jpg)
![KLOR](/docs/images/Klor_1.4_picture13.png)

### [CHANGELOG](https://github.com/Lefuneste83/KLOR/blob/main/CHANGELOG.md)

### [PCB FOR FULL HEIGHT SWITCHES (REV 1.4)](https://github.com/Lefuneste83/KLOR/tree/main/PCB/klor1_4)
-  This is my original initial design, derived from the 1.3 with lots of upgrades. I have built it and it works great. The south facing LED and the better suited LED packages make this the best choice for a first KLOR build. It keeps the overall design of the original in terms of PCB size and modularity. It is designed for MX style full height hotswap sockets. Gateron or Kailh sockets work great and probably other brands as well. This is not compatible with low profile sockets!

### [FABRICATION NOTES (FOR REV 1.4)](https://github.com/Lefuneste83/KLOR/blob/main/FABNOTES.md)
- These are my recommendations for first time builders of the KLOR keyboard. I suggest to have a read as they explain most tricky points that I have encountered while building mine.

### [PCB FOR LOW PROFILE GATERON KS33 SWITCHES (BETA VERSION REV 1.4 LP KS33)](https://github.com/Lefuneste83/KLOR/tree/main/PCB/klor1_4_LP_KS33)
-  This is a beta version derived from the 1.4 using low profile Gateron hotswap sockets for KS33 switches. It is a beta version so it will see lots of updates in the coming days. Don't rush to have it made except if you want to test it. In particular the haptic module will most likely interfere with the sockets and will require some filing of the haptic PCB. So it is not perfect yet.

### [PCB FOR ALTERNATIVE HAPTIC MODULE](https://github.com/Lefuneste83/KLOR/tree/main/PCB/Alternate%20DIY%20Haptic%20Module)
-  This is an alternative version of the haptic module for those who don't want to spend a fortune on the original one or can't source it. It is for advanced users as you will need some experience in SMD soldering and a hot air or hot plate to solder the linear actuator, and some form of magnification for the driver chip. It works great and is a bit shorter for easier integration. It mounts perfectly on all PCB versions except most likely on the low profile PCB because of the interference with the hotswap socket.

### [PCB FOR FULL HEIGHT SWITCHES CORRECTED STOCK VERSION (REV 1.3)](https://github.com/Lefuneste83/KLOR/tree/main/PCB/klor1_3)
-  This is as close as it gets to the original design but with some rerouting to allow to pass JLCPCB preproduction validation process. It uses the older style of LED (WS2812 3535) which are very tricky to solder properly, as they are not intended to be mounted this way. I strongly suggest moving to the 1.4 version for a much better build experience and a much more reliable build.

### [FIRMWARE](https://github.com/Lefuneste83/KLOR/blob/main/FIRMWARE.md)
-  VIAL support is now working on RP2040 with VIAL-QMK
-  These are updated QMK and ZMK config files and compiled images. They should have most devices enabled by default and should compile on latest toolchains of ZMK and QMK. A [Github Actions repositiry for ZMK](https://github.com/Lefuneste83/zmk-config-klor) is also available in my other repositories. Keep in mind that I only use ZMK on NRF52840 and QMK on RP2040. I would advise you to do the same as Atmega chips will not support all functionalities of the KLOR keyboard. As a reminder ZMK on NRF52840 will not support audio or haptic yet, but will support OLED to a certain degree and wireless communications with BLE protocol. QMK on RP2040 will support everything except wireless communications.

# CONTEXT
I have just completed my build of the 1.3 and found it a bit frustrating to assemble, despite my 13 year experience with this kind of project. Don't get me wrong the KLOR project is absolutely marvelous, but the PCB design starts to show its age IMHO, in the details of the layout in particular. Technology wise it is one, if not the best project out there hands down.

So here you will find a completely refactored PCB design of the KLOR project for 2024 including :

- Much better suited and easier to solder ARGB modules. I have used SK6812 Mini-E (aka 6028 size LED) version as it is the typical choice for this kind of keyboard application. I have thus kept the original paradigm of through hole design, with a symetrical front/back layout, but while using a LED module which is designed for this application, contrary to the original model WS2812 3535 which required a direct "hanged" soldering, with very likely damages to the plastic package as well as missalignment issues, as this part is designed for direct surface mount. I personnaly think that it would be even better to use the new WS2812 2020 package which is very neat, but as this is a strictly SMD part, there is no need for discrete cutouts anymore, so the design would look a bit different. Also you need to master SMD soldering. Let me know if you are interested in this type of LED package, I could make a forked design without too much fuss.

- As Hipyo Tech can confirm, we are in 2024 so no North facing LED are allowed anymore. I have moved to South facing LED.

- I have tried to keep the overall design paradigm so all the good stuff is still there!!

- I have very extensively refactored the PCB layout (3 days of intense work) to clean up the various little issues that were sprinkled around the original design including :

  
  Rerouting of 90% of the PCB. Healthier and more rational overall routing, at least that's my belief...
  
  Change to the footprint of the solder jumpers to triangular shapes much easier to bridge
  
  Correction of missing ground connections on the various switches bodies
  
  Dual ground planes thorough validation (this was painful)
  
  Very slight changes to the board cutout on the right side, to deal with reversed switch placement. Also very slight reduction of the cutout under the top of the MCU to catter some track celearance that would pop up in DRC. This should have no impact as this cutout serves no real purpose as far as I know. Cases and switchboards should mount the same, except for the ones using the puck cutout (see below).
  
  Very slight movement of the puck mounting holes downward (98.57 mm instead of 96.4 mm) by a couple milimeters to catter for reversed switches pad postions. I could not do otherwise without revisiting the switch layouts. I could not solve this by rotating the 3 mounting holes without interfering with other nets. It should not affect the mounting ability of the puck itself, but it WILL interfere with existing back cases using the puck cutout. So we will need specific cutouts for the case. As I don't have access to the original step model the best option would be to use some alternate case design provided with source files in order to lower the cutout by the same amount (2.17 mm).
  
  I managed a 0 error JLCPCB DRC, with only very few voluntary exceptions (down from 1000+). It took me several hours to clean up the various little issues that were sprinkled all around the orignial design. And I can confirm that Kicad on Linux is not a pleasure to use...
  
  Change of Logo with mine !

  This repo will be updated as I have new ideas for integrations of various tech or correction for errors.

  I have also included files for a working 1.3 design which passes the JLCPCB fabrication and is working as a real world product (REV 1.3)
  
***

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/images/klor-font-logo-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="/docs/images/klor-font-logo-bright.svg">
  <img alt="KLOR logo font" src="/docs/images/klor-font-logo-bright.svg">
</picture>


# KLOR SPLIT KEYBOARD

KLOR is a 36-42 key column-staggered split keyboard. It supports a per-key RGB matrix, encoders, OLED displays, haptic feedback, speakers, a Pixart Paw3204 trackball, the [SplitKB tenting puck](https://splitkb.com/products/tenting-puck), and four different layouts, through break-off parts.

***

## RENDERING OF THIS FORK (Rev 1.4)

![KLOR layouts](/docs/images/Klor_1.4_picture4.png)
![KLOR layouts](/docs/images/Klor_1.4_picture5.png)
![KLOR layouts](/docs/images/Klor_1.4_picture1.png)
![KLOR layouts](/docs/images/Klor_1.4_picture2.png)
![KLOR layouts](/docs/images/Klor_1.4_picture3.png)

***

## LAYOUTS

![KLOR layouts](/docs/images/klor-layouts.svg)

***

## PCB 

[Here](/PCB/) you can find the KiCad files and Gerbers for the KLOR 1.3 (tested working with JLCPCB) and 1.4 (this version). 

***

## CASE

[Here](/case/) are the case files for the KLOR. There is an acrylic case and a 3D printed case (which uses acrylic too) for every layout.

***

## SWITCHPLATE

In every case directory you'll find the matching switchplates as **.dxf**, **.svg**, **.stl**, and a **.zip**-file, containing gerber files for a FR4 plate.

***

## KNOB

You can use pretty much any knob, which works with the EC11 encoder, but [here](/knob/) you can find one, I designed for the KLOR.

***

## BUILD GUIDE

Here you can find the build guides for the KLOR.\
[KLOR build guide 3DP case](/docs/buildguide_3DP.md) (QMK)\
[KLOR build guide stacked acrylic case](/docs/buildguide_acrylic.md) (QMK)\
[KLOR BLE build guide 3DP case](/docs/buildguide_3DP_ble.md) (ZMK)\
[KLOR BLE build guide stacked acrylic case](/docs/buildguide_acrylic_ble.md) (ZMK)

***

## CHOC/KS27 VERSION

[Sadek Baroudi](https://github.com/sadekbaroudi) did an amazing job in creating a version of the KLOR which supports KS-27 and Choc V1 switches. Including a special case for it.\
[KLOR Sadek KS-27 and Choc V1 mod](https://github.com/sadekbaroudi/KLOR)

***

## CREDITS

The KLORs hardware is based on the [Sofle](https://github.com/josefadamcik/SofleKeyboard) by [Josef Adamcik](https://github.com/josefadamcik).\
Other inspirations are 
- [Kyria](https://splitkb.com/products/kyria-pcb-kit) by [Thomas Baart](https://github.com/splitkb)
- [Yacc46](https://github.com/1m38/keyboards/tree/main/yacc46) by [1m38](https://github.com/1m38)
- [Elephant42](https://github.com/illness072/elephant42) by [illness072](https://github.com/illness072)
- [Torn](https://github.com/rtitmuss/torn) by [Richard Titmuss](https://github.com/rtitmuss)
- [Claw44](https://github.com/yfuku/claw44) by [yfuku](https://github.com/yfuku)

I used the Pimoroni Haptic Buzz Footprint from the [Buzzard](https://github.com/crehmann/Buzzard) by [Christoph Rehmann](https://github.com/crehmann).

***

People who helped me create this board and fix stuff
- [KarlK90](https://github.com/KarlK90)
- [MangoIV](https://github.com/MangoIV)
- [OxCB](https://github.com/0xCB-dev)
- [MicroFortnight](https://github.com/microfortnight)
- [dreipunkteinsvier](https://github.com/dreipunkteinsvier)


If you build a KLOR I would be pretty happy to see some pictures. And if you want to leave me a tip you can do this [here](https://ko-fi.com/geigeigeist) (but please don't feel pressured)
