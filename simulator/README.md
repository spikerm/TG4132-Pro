# TR1604-Pro Windows simulator

This simulator renders the approved TR1604-Pro CRT layout on Windows and lets us
validate menus, markers and measurement workflows before the PCB is available.

## Requirements

- Windows 10 or 11
- Python 3.11 or newer from python.org
- During Python installation enable **Add Python to PATH** and install Tcl/Tk
  (included in the normal Windows installer)

No third-party Python packages are required.

## Start

Double-click:

```text
run_windows.bat
```

Or from PowerShell:

```powershell
cd simulator
py -3 tr1604_sim.py
```

## Current controls

| Key | Action |
|---|---|
| `F1` | Spectrum analyzer mode |
| `F2` | Duplex-filter mode |
| `F3` | Memory/trace mode |
| `F4` | Antenna-analyzer mode |
| `1`–`4` | Select and enable marker |
| Left/Right | Move selected marker |
| Shift + Left/Right | Fine marker step |
| Ctrl + Left/Right | Coarse marker step |
| Enter | Enter exact marker frequency |
| `N` | Move marker to nearest example notch |
| `P` | Move marker to center |
| `M` | Show/hide right menu |
| `B` | Enable/disable memory trace |
| `A` | Change averaging |
| `S` | Export the current canvas to PostScript |
| Escape | Close the menu |

## First milestone

Implemented now:

- resizable CRT window;
- approved green monochrome layout;
- duplex-filter response with two rejection notches;
- four configurable markers;
- exact marker frequency entry;
- marker fine/coarse movement;
- marker readout and delta calculation;
- optional stored-memory trace;
- right-side menu and bottom shortcut bar;
- synthetic live trace/noise.

## Next simulator work

1. Real screen classes for all nine approved modes.
2. Editable start, stop, center, span, RBW, VBW and TG level.
3. Preset/profile save and recall in JSON.
4. Trace A/B, max hold, min hold and averaging engine.
5. Duplex-filter acceptance limits and PASS/FAIL.
6. CAL OUT / CAL IN workflow.
7. CSV trace import and export.
8. Exact shared display-list format with the STM32 firmware vector renderer.
9. Automated screenshot regression tests.
