# TG4132-Pro firmware

Initial firmware target: **STM32F746G-DISCO** using PlatformIO and STM32Cube HAL.

## Current milestone

The first commit establishes the fail-safe application core before ADC, DAC, USB, SD or CRT timing drivers are connected.

Implemented:

- explicit operating modes: bypass, acquisition, stored trace, marker overlay and vector menu;
- mandatory fallback to analog bypass when power, ADC, DAC or watchdog status is unsafe;
- overlay ownership only during a confirmed CRT flyback interval;
- circular acquisition buffer;
- first vector marker primitive;
- 216 MHz STM32F746 clock setup.

## Build

```bash
cd firmware
pio run
```

## Safety model

The firmware never provides the primary bypass function. Normally-closed relays on the interface board carry original X/Y/Z signals when the board is unpowered. Firmware may energize the active path only after all startup self-tests pass.

## Next drivers

1. board I/O and relay-enable driver;
2. sweep/flyback detector input capture;
3. ADS8684A SPI acquisition;
4. dual-DAC DMA output;
5. Z blanking output;
6. USB HID keyboard host;
7. SD/FatFs trace storage;
8. vector font renderer and menu engine.
