# TR1604-Pro iPhone Simulator

SwiftUI iPhone simulator for the TR1604-Pro instrument UI.

## Design goals

- Landscape-only CRT-style display.
- No Wi-Fi and no Bluetooth code.
- Local simulation works fully offline.
- Separate `USBInstrumentDataSource` transport boundary for a future wired accessory implementation.
- Same functional groups as the Windows simulator: Spectrum, Duplex, Memory, Antenna, Insertion Loss and Setup.
- Four markers, Delta display, TG status, memory state and a maximum of 12 visible menu rows.

## Generate the Xcode project

Install XcodeGen on a Mac, then from this directory run:

```bash
xcodegen generate
open TR1604ProSimulator.xcodeproj
```

Choose your iPhone or an iPhone simulator as the run destination and build the `TR1604ProSimulator` target.

## Current controls

- F1 Spectrum
- F2 Duplex
- F3 Memory
- F4 Antenna
- F5 selects the next marker
- F6 moves the selected marker to the strongest peak
- F7 Insertion Loss
- F8 Setup
- MENU ON/OFF hides or shows the 12-row context menu
- Tap a marker block to select and enable/disable that marker
- Tap a context-menu item to select and execute supported actions

## Wired mode

`DataSourceMode.usb` and `USBInstrumentDataSource` intentionally contain no radio/network implementation. The first release remains a local simulator. The transport interface is isolated so a future wired iPhone accessory protocol can feed the same `InstrumentSnapshot` model without changing the CRT renderer.
