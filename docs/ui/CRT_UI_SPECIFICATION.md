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
- configurable markers;
- right-side spectrum menu.

### 3. Marker system

Markers are fully user-configurable and are never permanently tied to fixed frequencies.

Required functions:

- at least four independent normal markers, with architecture prepared for ten;
- per-marker enable/disable;
- direct numeric frequency entry;
- movement with cursor keys, encoder or configurable frequency step;
- marker-to-peak;
- next peak left/right;
- marker-to-center;
- marker-to-start and marker-to-stop;
- marker-to-minimum/notch;
- automatic peak or notch tracking;
- normal, delta and fixed-reference marker modes;
- selectable active marker;
- marker frequency, level and trace assignment;
- marker table;
- marker labels and optional user names;
- marker presets stored per measurement profile.

Delta mode uses one marker as reference and reports frequency and level difference for another marker. Moving the reference marker updates all associated delta readings.

Numeric entry examples:

- `430.3625 MHz`
- `431.9625 MHz`
- `1.6000 MHz` delta target

These values are examples and may be saved as a duplex-filter preset, but remain editable.

### 4. Duplex filter tune mode

This is a primary application mode.

Required fields:

- two or more user-configurable notch markers;
- notch depth at every enabled notch marker;
- delta frequency between selected markers;
- passband insertion loss;
- bandwidth and Q where applicable;
- calibration state;
- TG level;
- memory/reference state;
- alignment PASS/FAIL against user-defined limits.

Default example preset:

- marker 1: `430.3625 MHz`;
- marker 2: `431.9625 MHz`;
- expected delta: `1.6000 MHz`.

The user can edit, replace and save these frequencies for other duplexers, cavity filters and channel spacings. Presets must store marker frequencies, limits, span, center, RBW, TG level and trace settings.

### 5. Zoom / notch detail

A narrow-span view around one selected marker or notch with:

- marker/notch center;
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
- configurable marker readout;
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
- marker preset management;
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

Approximately 18–25% of the usable screen width. It contains menu items, active-marker readout and mode-specific values.

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

- cursor keys for marker movement;
- numeric frequency entry;
- Enter and Escape;
- function keys;
- direct marker selection shortcuts;
- configurable marker step size;
- dedicated shortcuts for marker, memory, TG and save;
- optional encoder and front-panel keys later.

Suggested shortcuts:

- `M`: marker menu;
- `1`–`9`: select marker;
- arrow left/right: move active marker;
- Shift + arrow: fine movement;
- Page Up/Down: coarse movement;
- `P`: marker to peak;
- `N`: marker to notch/minimum;
- `D`: delta mode;
- `C`: marker to center;
- Enter: numeric marker frequency entry.

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
4. Marker frequencies are freely editable and can be saved in presets.
5. Duplex-filter mode supports arbitrary user-entered notch frequencies and limits.
6. A hardware or firmware fault returns the analyzer to original bypass operation.
