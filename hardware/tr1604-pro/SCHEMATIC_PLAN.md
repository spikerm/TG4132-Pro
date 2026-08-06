# TR1604-Pro schematic plan

## Product scope

A direct-fit digital-memory, CRT-overlay and tracking-generator controller for the TR4132/TR4132N. The CRT remains the only display.

## Hierarchical sheets

1. `01_CONNECTORS_BYPASS`
   - P1 power: GND, +5 V, +15 V, -15 V
   - P2/P3 X/Y/Z signal and returns
   - normally-closed relay bypass for X, Y and Z
   - test points and cable shields

2. `02_POWER`
   - protected +5 V digital input
   - low-noise 3V3 digital rail
   - low-noise 5 V analog rail
   - retained +/-15 V analog rails
   - power-good, brownout and relay-safe control

3. `03_STM32H743`
   - STM32H743VIT6
   - HSE crystal, SWD, QSPI flash, watchdog
   - USB-A host for keyboard
   - USB-C device/service
   - SDMMC microSD

4. `04_XY_ACQUISITION`
   - ADS8684A for X, Y, Z monitor and AUX
   - protected bipolar inputs
   - anti-alias filtering
   - calibration source and test points

5. `05_VECTOR_DAC`
   - dual simultaneous-update 16-bit DAC
   - bipolar X/Y output amplifiers
   - gain and offset calibration
   - DMA-driven LDAC timing

6. `06_Z_BLANKING`
   - Z polarity detection
   - fail-safe original pass-through
   - overlay blanking and intensity control

7. `07_MEMORY_ENGINE`
   - external SDRAM or SRAM buffer
   - minimum 16k X/Y points per trace
   - four reference slots
   - live, max-hold, min-hold and average traces
   - trace metadata and CRC

8. `08_TRACKING_GENERATOR_INTERFACE`
   - SPI, I2C, trigger, RF enable and PLL-lock lines
   - 5 V and 3V3 power to RF board
   - sweep-start and sample-clock outputs
   - optional 10 MHz reference input footprint, DNP by default

9. `09_FRONT_PANEL_IO`
   - USB keyboard host
   - SD card
   - status LEDs
   - trigger out, marker out and external modulation input

10. `10_TEST_CALIBRATION`
    - loopback paths
    - DAC-to-ADC calibration
    - relay test
    - factory test header

## Memory function

The original TR1604 stored two 8-bit, 512-point traces. TR1604-Pro will store complete 16-bit traces in RAM and on SD.

Initial target:

- 16,384 samples per acquisition;
- X, Y and status word per sample;
- four fast reference slots in RAM;
- unlimited named traces on microSD;
- live, A, B, A-B, max hold, min hold and average modes;
- CSV export and BMP screenshot rendered from vector data.

## Tracking-generator relationship

The tracking generator is a separate shielded RF board, but its control interface is part of the main schematic from Rev A. The main MCU derives frequency from the acquired X ramp and commands the RF synthesizer. Y is used for normalized scalar response measurements.

## CRT menu concept

The CRT overlay uses vector strokes, not raster video. During flyback or a controlled display takeover, the DACs generate X/Y vectors and Z controls beam visibility. Menu pages use large single-stroke characters and limited line density to avoid flicker.
