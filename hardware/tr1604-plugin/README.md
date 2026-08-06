# TG4132-Pro TR1604 plug-in board

## Status

Architecture started. Electrical values and converter selection are provisional until the analyzer-side X, Y and Z signals have been measured.

## KiCad project plan

Project name: `TG4132_TR1604_Plugin`

Hierarchical sheets:

1. `01_TR1604_CONNECTORS.kicad_sch`
2. `02_POWER_AND_PROTECTION.kicad_sch`
3. `03_XY_ACQUISITION_ADS8684A.kicad_sch`
4. `04_XY_VECTOR_DAC.kicad_sch`
5. `05_XY_FAILSAFE_SWITCHING.kicad_sch`
6. `06_Z_BLANKING_INTERFACE.kicad_sch`
7. `07_CONTROLLER_INTERFACE.kicad_sch`
8. `08_SD_USB_AND_EXPANSION.kicad_sch`
9. `09_TEST_AND_CALIBRATION.kicad_sch`

## Rev A provisional parts

| Function | Provisional choice | Status |
|---|---|---|
| X/Y/AUX ADC | ADS8684A | selected for schematic start |
| X/Y DAC | dual 16-bit simultaneous DAC, >=1 MSPS/ch | open |
| X/Y bypass | normally-closed signal relays | required |
| fast overlay switch | low-distortion bipolar analog switch | open |
| analog buffers | low-offset, fast op-amps on +/-15 V-derived rails | open |
| controller | STM32F746 development platform | selected for prototype |
| storage | microSD on controller | selected for prototype |
| keyboard | USB host on controller | selected for prototype |

## First schematic task

Draw the analyzer connector, power connector and three completely passive fail-safe bypass paths first. Only after those pass ERC will active acquisition and overlay blocks be attached.
