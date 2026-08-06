# CRT UI implementation plan

This plan implements the approved `docs/ui/CRT_UI_SPECIFICATION.md` design on the STM32H743.

## Software layers

```text
application modes
    spectrum / tracking / duplex / antenna / memory / setup
                         |
UI scene manager and input dispatcher
                         |
widgets: labels, values, menus, grids, markers, plots
                         |
vector font and geometry generator
                         |
frame scheduler / brightness and dwell limiter
                         |
DAC DMA + Z blanking + X/Y switch ownership
```

## Source tree target

```text
firmware/
  include/ui/
    ui.h
    ui_scene.h
    ui_input.h
    ui_theme.h
    ui_layout.h
    vector_font.h
    vector_path.h
    widgets.h
  src/ui/
    ui.c
    ui_scene.c
    ui_input.c
    vector_font.c
    vector_path.c
    widgets.c
    screen_startup.c
    screen_spectrum.c
    screen_markers.c
    screen_duplex.c
    screen_notch_zoom.c
    screen_insertion_loss.c
    screen_memory.c
    screen_antenna.c
    screen_setup.c
```

## Coordinate system

Use normalized signed coordinates independent of final DAC gain:

- X: `0 .. 65535`
- Y: `0 .. 65535`
- origin at lower left in UI space;
- hardware conversion may invert either axis;
- safe margin around the CRT edge is configurable.

## Vector primitive

```c
typedef struct {
    uint16_t x;
    uint16_t y;
    uint8_t beam_on;
    uint8_t intensity;
} UiVectorPoint;
```

Required primitives:

- move;
- line;
- polyline;
- rectangle;
- tick/grid generator;
- 5x7 and compact vector characters;
- marker triangle and vertical line;
- trace resampling;
- Smith-chart arcs for Rev B.

## Frame construction

Each scene generates layers in this order:

1. blanked move to safe origin;
2. fixed borders and grid;
3. trace or traces;
4. markers;
5. numeric readouts;
6. right-side menu;
7. bottom status bar;
8. blanked return.

Static and dynamic layers are cached separately. A trace update must not regenerate unchanged labels or menu geometry.

## Refresh strategy

- hardware acquisition remains independent of CRT rendering;
- UI target: 20–40 complete vector frames/s where practical;
- trace-only refresh can be faster than full UI refresh;
- menu and labels update only when values change;
- maximum vector count and dwell time are enforced;
- watchdog forces bypass if the DAC/DMA scheduler stalls.

## Scene states

```c
typedef enum {
    UI_SCREEN_STARTUP,
    UI_SCREEN_SPECTRUM,
    UI_SCREEN_MARKERS,
    UI_SCREEN_DUPLEX,
    UI_SCREEN_NOTCH_ZOOM,
    UI_SCREEN_INSERTION_LOSS,
    UI_SCREEN_MEMORY,
    UI_SCREEN_ANTENNA,
    UI_SCREEN_SETUP
} UiScreen;
```

## Duplex mode data model

```c
typedef struct {
    double marker1_hz;
    double marker2_hz;
    float marker1_db;
    float marker2_db;
    float passband_loss_db;
    float notch1_depth_db;
    float notch2_depth_db;
    float delta_db;
    bool calibration_ok;
    bool limits_pass;
} DuplexMeasurement;
```

Default preset:

- marker 1: `430362500 Hz`
- marker 2: `431962500 Hz`
- delta: `1600000 Hz`

The limits system must allow independent minimum rejection and maximum insertion-loss requirements.

## Keyboard defaults

- `F1`: Spectrum
- `F2`: Tracking generator
- `F3`: Duplex filter
- `F4`: Antenna analyzer
- `F5`: Markers
- `F6`: Memory
- `F7`: Save/recall
- `F8`: Setup
- `M`: marker menu
- `D`: delta marker
- `P`: marker to peak
- `T`: TG on/off
- `S`: store current trace
- `R`: recall trace
- arrows: move marker/menu selection
- Page Up/Page Down: coarse value adjustment
- Enter: select/edit
- Escape: back

## First implementation milestones

1. Vector DAC loopback test with rectangle and grid.
2. Compact vector font and static startup screen.
3. Keyboard navigation and right-side menu.
4. Live trace resampling and spectrum screen.
5. Marker and delta-marker engine.
6. Duplex-filter mode with the approved frequencies.
7. Memory/reference traces and SD storage.
8. Tracking-generator controls and calibration.
9. Antenna scalar mode.
10. Rev B vector RF/Smith chart support.

## UI test method

A desktop simulator should render the same vector list into SVG or PNG. Golden-image tests compare simulated screens against approved layouts before flashing the hardware.
