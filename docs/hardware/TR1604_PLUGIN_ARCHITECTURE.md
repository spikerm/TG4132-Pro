# TR1604-compatible plug-in architecture

## Purpose

This board is a modern replacement/interface module for the original TR1604 digital-memory signal path. It is installed between the TR4132/TR4132N signal source and the CRT driver and handles the same six analog signals:

- `X_IN`  – original analyzer horizontal ramp into the plug-in;
- `X_OUT` – horizontal signal returned to the CRT driver;
- `Y_IN`  – original analyzer vertical/video signal into the plug-in;
- `Y_OUT` – vertical signal returned to the CRT driver;
- `Z_IN`  – original analyzer blanking/intensity signal into the plug-in;
- `Z_OUT` – blanking/intensity signal returned to the CRT driver.

The service-manual TR1604 schematic also shows the available supply rails `+15 V`, `-15 V`, `+5 V` and ground on a separate connector.

## Safety and fail-safe rule

Loss of plug-in power, firmware failure, watchdog timeout or an unconnected controller must leave the spectrum analyzer usable in its original analog mode.

Revision A therefore uses normally-closed signal relays for X and Y pass-through. Z pass-through must also default to the original signal without firmware intervention. Semiconductor switches may be added for fast overlay selection, but they may not be the only bypass mechanism.

## Functional blocks

```text
TR4132 X_IN ----+---- NC relay bypass --------------------+---- X_OUT to CRT
                |                                         |
                +--> protected ADC input                  +<-- overlay DAC/buffer

TR4132 Y_IN ----+---- NC relay bypass --------------------+---- Y_OUT to CRT
                |                                         |
                +--> protected ADC input                  +<-- overlay DAC/buffer

TR4132 Z_IN ----+---- default-pass blanking path ----------+---- Z_OUT to CRT
                |                                         |
                +--> logic comparator                     +<-- overlay blanking
```

## Revision A controller strategy

The first prototype uses the existing STM32F746-based hardware as the UI/controller during development. The internal plug-in board contains the analog acquisition, DAC, switching, protection and power-conditioning circuits. A later compact controller board can replace the development platform without changing the analyzer-side connector.

## Proposed converters

### Acquisition

- ADS8684A, 16 bit, four bipolar input channels.
- CH1: X input.
- CH2: Y input.
- CH3: Z/blanking observation after conditioning.
- CH4: auxiliary detector or internal calibration channel.

Exact input ranges and filter constants remain provisional until X, Y and Z are measured in the actual analyzer.

### Vector output

Two simultaneously updated DAC channels are required for X and Y. Minimum design targets:

- 16-bit resolution;
- at least 1 MSPS per channel for simple vector text and markers;
- hardware simultaneous update/latch;
- external precision reference;
- output buffers operating from bipolar analog rails.

The final DAC part is intentionally not frozen before timing and voltage measurements.

## Connector definition from the TR1604 schematic

The available drawing shows a 15-position signal interconnect and the following labelled positions:

| Pin | Label | Direction relative to plug-in |
|---:|---|---|
| 3 | `Y_OUT` | output to CRT driver |
| 5 | `Y_IN` | input from analyzer |
| 7 | `X_OUT` | output to CRT driver |
| 9 | `X_IN` | input from analyzer |
| 11 | `Z_OUT` | output to CRT driver |
| 13 | `Z_IN` | input from analyzer |

The drawing does not label the remaining positions. They must not be assigned until continuity checks or further documentation confirms their use.

The power connector shown in the same schematic is:

| Pin | Rail |
|---:|---|
| 1 | GND |
| 2 | +5 V |
| 3 | +15 V |
| 4 | -15 V |
| 5 | not labelled |

## Overlay operating modes

1. **Bypass** – all original signals pass through unchanged.
2. **Acquire** – original signals pass through while X/Y/Z are sampled.
3. **Marker overlay** – original trace remains active; short vector marker cycles are inserted.
4. **Menu/vector display** – CRT is temporarily taken over to draw text or menus.
5. **Stored trace** – sampled data is replayed through the X/Y DACs.

## Measurements required before schematic freeze

- X input and output DC range, polarity and source impedance.
- Y input and output DC range for 10 dB/div, 5 dB/div and linear modes.
- Z input/output active polarity and voltage levels.
- Sweep period and flyback duration at minimum and maximum scan time.
- Required X/Y settling time at the CRT-driver input.
- Current available from the +15 V, -15 V and +5 V rails.
- Exact connector family, pitch, keying and cable orientation.

## Revision A design sheets

1. `01_TR1604_CONNECTORS`
2. `02_POWER_AND_PROTECTION`
3. `03_XY_ACQUISITION_ADS8684A`
4. `04_XY_VECTOR_DAC`
5. `05_XY_FAILSAFE_SWITCHING`
6. `06_Z_BLANKING_INTERFACE`
7. `07_CONTROLLER_INTERFACE`
8. `08_SD_USB_AND_EXPANSION`
9. `09_TEST_AND_CALIBRATION`

## Non-negotiable constraints

- No connection to the CRT high-voltage section.
- No permanent cutting of original PCB traces.
- Original operation must return automatically when the plug-in is unpowered.
- All analyzer-side signal pins require current limiting and overvoltage protection.
- Analog ground routing and chassis bonding must be documented before PCB release.
