# TG4132-Pro firmware

Production MCU target: **STM32H743VIT6** on the custom TR1604-Pro main PCB. No LCD or touchscreen is required; the original TR4132 CRT is the display.

For early firmware development, PlatformIO uses the `nucleo_h743zi` environment because it provides the same STM32H743 family and an accessible debugger. Pin assignments remain isolated in the board-support layer so they can be moved to the production PCB.

## Why STM32H743

- sufficient timer and DMA performance for deterministic X/Y vector generation;
- USB host support for a standard USB keyboard;
- SDMMC for trace, screenshot and settings storage;
- multiple SPI peripherals for ADS8684A, vector DAC and the later RF generator;
- enough internal RAM for traces, vector lists and filesystem buffers;
- no display hardware or external SDRAM required for Revision A.

## Current milestone

Implemented:

- explicit operating modes: bypass, acquisition, stored trace, marker overlay and vector menu;
- mandatory fallback to analog bypass when power, ADC, DAC or watchdog status is unsafe;
- overlay ownership only during a confirmed CRT flyback interval;
- circular acquisition buffer;
- first vector marker primitive;
- STM32H743 bring-up clock configuration at 400 MHz.

## Build

```bash
cd firmware
pio run
```

## Safety model

The firmware never provides the primary bypass function. Normally-closed relays on the interface board carry original X/Y/Z signals when the board is unpowered. Firmware may energize the active path only after all startup self-tests pass.

## Next drivers

1. production-board GPIO and relay-enable driver;
2. sweep/flyback detector input capture;
3. ADS8684A SPI acquisition;
4. simultaneous dual-DAC DMA output;
5. Z blanking output;
6. USB HID keyboard host;
7. SDMMC/FatFs trace storage;
8. vector font renderer and CRT menu engine.
