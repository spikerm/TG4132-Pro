# TR1604-Pro Instrument Core

The Instrument Core is the hardware-independent measurement layer for the TR1604-Pro.

## Architecture

- `state.py` - shared instrument state and configuration
- `sweep.py` - frequency axis and sweep acquisition
- `trace.py` - clear/write, max hold, min hold, average, view and Trace B memory
- `marker.py` - four markers, peak/notch positioning and Delta marker state
- `measurement.py` - bandwidth, Q, ripple, notch depth and SWR/return-loss math
- `menu.py` - 12-row menu viewport and paging
- `storage.py` - profile/trace persistence abstraction
- `usb.py` - USB CDC transport abstraction for the future STM32 link
- `calibration.py` - RF reference and OPEN/SHORT/LOAD calibration state
- `core.py` - central `InstrumentCore` facade

## Desktop integration

`../tr1604_sim_core.py` uses the V7.2.2 CRT renderer as the display backend while every raw sweep is also processed by `InstrumentCore`.

The first migrated functions are:

- Marker to Peak
- Marker to Notch
- Bandwidth / Q calculation
- Shared sweep and marker state

The remaining V7.2 functions can now be migrated engine-by-engine without changing the CRT layout.

## STM32 direction

The STM32 firmware should implement hardware-specific adapters for:

1. ADC / IF sample source
2. Tracking-generator synthesizer
3. CRT/vector DAC output
4. USB CDC transport
5. SD/FatFS storage

The measurement, marker, menu and state logic should remain compatible with the desktop Instrument Core API.
