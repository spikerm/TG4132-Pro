# TR1604-Pro CRT UI specification

Status: **approved design baseline**

This document defines the software user interface for the TR1604-Pro. The approved CRT slideshow is the visual reference for implementation. The original TR4132N CRT remains the only display.

## Design language

- Monochrome green vector graphics.
- Classic Takeda Riken / HP / Agilent instrument layout.
- Large measurement area with a narrow right-hand information/menu column.
- Bottom status and mode bar.
- No modern desktop-style windows.
- Menus must not unnecessarily cover the active trace.
- Text, traces, markers and menu separators are drawn as CRT vectors.
- The UI must remain readable on the real CRT at normal intensity and focus.

## Screen set

### 1. Startup / title

Displays:

- `TAKEDA RIKEN`
- `TR1604-PRO`
- `DIGITAL MEMORY & TRACKING GENERATOR`
- target analyzer type;
- firmware version;
- initialization progress;
- self-test result.

The analyzer remains in hardware bypass until startup tests pass.

### 2. Spectrum analyzer

Main trace view with:

- reference level;
- dB/div;
- attenuation;
- RBW and VBW;
- center/start/stop/span;
- sweep time;
- TG state and level;
- one or two markers;
- right-side spectrum menu.

### 3. Marker readout

Supports:

- marker 1 and marker 2;
- marker-to-peak;
- next peak;
- marker-to-center;
- delta frequency and level;
- marker table;
- automatic peak tracking.

### 4. Duplex filter tune mode

This is a primary application mode.

Required fields:

- marker 1 at `430.3625 MHz`;
- marker 2 at `431.9625 MHz`;
- delta `1.6000 MHz`;
- notch depth at both frequencies;
- passband insertion loss;
- bandwidth and Q where applicable;
- calibration state;
- TG level;
- memory/reference state;
- alignment PASS/FAIL against user-defined limits.

The displayed response uses deep rejection notches at the specified frequencies. This mode is intended for tuning duplex cavities and duplex filters where the selected frequencies must be strongly attenuated.

### 5. Zoom / notch detail

A narrow-span view around one selected notch with:

- notch center;
- depth;
- -3 dB or user-selected bandwidth;
- Q;
- live marker tracking;
- finer frequency steps.

### 6. Insertion-loss view

Displays passband loss over a selected frequency interval, including:

- point readings;
- minimum, maximum and average insertion loss;
- optional reference normalization;
- acceptance limits.

### 7. Memory / trace comparison

Trace modes:

- live trace A;
- stored trace B;
- A-B;
- B-A;
- reference 1 through 4;
- max hold;
- min hold;
- averaging;
- persistence.

Stored traces can be written to and recalled from SD.

### 8. Antenna analyzer

Rev A scalar functions:

- return loss;
- SWR;
- resonance;
- bandwidth;
- marker readout;
- reference calibration.

Rev B vector functions:

- complex impedance;
- R and X;
- phase;
- Smith chart.

### 9. System setup

Includes:

- frequency setup;
- amplitude setup;
- sweep setup;
- marker setup;
- trace/memory setup;
- disk/USB;
- calibration;
- system information;
- firmware update;
- diagnostic and service pages.

## Persistent screen regions

### Top status line

Recommended contents:

- analyzer and accessory identification;
- active mode;
- TG status and output level;
- time;
- warning state.

### Main plot

Approximately 75–82% of the usable screen width in normal modes.

### Right information column

Approximately 18–25% of the usable screen width. It contains menu items, marker readout and mode-specific values.

### Bottom status bar

Shows active mode shortcuts and critical state:

- Spectrum Analyzer
- Tracking Generator
- Duplex Filter
- Antenna Analyzer
- Marker Table
- Memory Save/Recall
- System Setup

## Input model

Primary control is a USB keyboard. The firmware must support:

- cursor keys;
- numeric entry;
- Enter and Escape;
- function keys;
- dedicated shortcuts for marker, memory, TG and save;
- optional encoder and front-panel keys later.

## Rendering constraints

- Vector rendering only; no bitmap framebuffer is assumed.
- Separate geometry layers for grid, trace, text, markers and menu.
- Limit point count per frame to preserve CRT refresh and brightness.
- Prefer static redraw only when content changes.
- Trace refresh has priority over menu animation.
- Automatic simplification of dense text and graphs for the real CRT.
- Avoid excessive dwell at a single coordinate to prevent bright spots or phosphor damage.

## Acceptance criteria

The implementation is accepted when:

1. All nine approved screen types are available.
2. The real CRT resembles the approved slideshow at normal viewing distance.
3. Menus remain readable without obscuring the measurement.
4. Duplex-filter mode clearly reports the rejection at 430.3625 and 431.9625 MHz.
5. A hardware or firmware fault returns the analyzer to original bypass operation.
