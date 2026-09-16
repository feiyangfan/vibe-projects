# FIRMWARE
My version of ZMK firmware  with Github Actions pipeline is [located here](https://github.com/Lefuneste83/zmk-config-klor):

It has both encoders working, precise pulse per rotation adjustments and RGB enabled by default.

Config files for both QMK and ZMK can be [found here](https://github.com/Lefuneste83/KLOR/tree/main/FIRMWARE):

For extra convienence if you intend to modify your firmware for a smaller layout, I have created a link to :

 -  A [full POLYDACTYL layout](http://www.keyboard-layout-editor.com/#/gists/8ff2b448f2ef6c56c2b932e83ebf040f)
 -  A [KONRAD layout](http://www.keyboard-layout-editor.com/#/gists/49ff09e68b46feb39760467424a4601a)
 -  A [YUBITSUME layout](http://www.keyboard-layout-editor.com/#/gists/dc3fdb427b3102ccbf85252e2e278918)
 -  A [SAEGEWERK layout](http://www.keyboard-layout-editor.com/#/gists/b3775d73a84de0d544ea3bf84bafb047)

****

-  Added support for VIAL firmware for RP2040 boards. You can now compile :
   
      the "default" layout using [QMK toolchain](https://github.com/qmk/qmk_firmware) and the command :

            qmk compile -kb electronlab/klor -km default -c
   
      or "vial" layout using [vial-qmk toolchain](https://github.com/vial-kb/vial-qmk) and the command :

            make clean && make electronlab/klor:vial
    
-   Also be aware that I have now enabled firmware based handedness definition ([#define EE_HANDS setting](https://docs.qmk.fm/features/split_keyboard)) so you should flash the firmware using the following commands for left and right keyboard sides :
-   
   For QMK environment
    
             qmk flash -kb electronlab/klor -km default -c -bl uf2-split-left
             qmk flash -kb electronlab/klor -km default -c -bl uf2-split-right
    
  For VIAL-QMK environment
     
             qmk flash -kb electronlab/klor -km vial -c -bl uf2-split-left
             qmk flash -kb electronlab/klor -km vial -c -bl uf2-split-right

-  Make sure you switch your serial communication to HALF DUPLEX as software pin swap used for full duplex does not seem to work well with firmware based handedness detection. If you alyays want to plug one side of the keyboard then you can set the master side in config.h and switch to full duplex with software pin swap. This will require a little testing but it will work eventually

-  While playing with QMK I have noticed that the original 1.3 design carried a wiring flaw on the minijack footprint and PCB traces. The RX/TX are symetrical between the two sides which makes it impossible to define the transmission protocol in QMK as serial full duplex with RP2040 ProMicro boards if you don't specify a pin swap command. By default the stock firmware uses bitbang driver on a single pin which is not optimal and made the use of a TRRS link unnecessary as 3 pins cable would suffice. If you use these boards you should set the following in the config.h for QMK if using RP2040 ProMicro boards.
      
                  //Full Duplex communication
                  #define SERIAL_USART_TX_PIN GP4     // USART TX pin
                  #define SERIAL_USART_RX_PIN GP1     // USART RX pin
                  #define SERIAL_USART_FULL_DUPLEX
                  #define SERIAL_USART_PIN_SWAP

-  In case your MCU can only use a single pin for communications, it is recommended to use half duplex serial instead of bitbang.
      
                  //Half Duplex communication
                  //#define SERIAL_USART_TX_PIN GP1     // USART TX pin
       
-  More about this matter [here](https://docs.qmk.fm/drivers/serial)
