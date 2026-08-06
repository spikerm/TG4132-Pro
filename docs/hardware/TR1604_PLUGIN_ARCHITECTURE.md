# TR1604-compatible plug-in architecture

## Purpose

This board is a modern replacement/interface module for the original TR1604 digital-memory signal path. It is installed between the TR4132/TR4132N signal source and the CRT driver and handles the same six analog signals:

- `X_IN`  – original analyzer horizontal ramp into the plug-in;
- `X_OUT` – horizontal signal returned to the CRT driver;
- `Y_IN`  – original analyzer vertical/video signal into the plug-in;
- `Y_OUT` – vertical signal returned to the CRT driver;
- `Z_IN`  – original analyzer blanking/intensity signal into the plug-in;
- `Z_OUT` – blanking/intensity signal returned to the CRT driver.

The original TR1604 drawings confirm that the module uses a dedicated signal connector, a separate ground-return connector and a separate power connector carrying `+15 V`, `-15 V`, `+5 V` and ground.

## Confirmed original TR1604 architecture

The six supplied PM074 schematic sheets show the following original implementation:

- a four-pole mechanical `MEMORY ON/OFF` switch (S386) switches X, Y and Z between direct bypass and memory operation;
- a nominal `1 MHz` timing generator clocks the acquisition and replay logic;
- the X channel is conditioned by bipolar op-amp stages and converted into the horizontal memory address sequence;
- the Y channel is sampled, converted and stored as eight data bits (`MD1` through `MD8`);
- the memory contains four 1K x 4 static RAM devices, arranged as two 8-bit trace memories;
- the stored X ramp and Y trace are reconstructed with separate D/A and output amplifier stages;
- X and Y output stages include front-panel gain and position adjustments;
- Z/blanking is switched and regenerated separately.

This proves that the desired modern design is electrically compatible with the original Advantest concept: acquire the analyzer's X/Y signals, then replay or substitute X/Y/Z signals ahead of the CRT driver.

## Safety and fail-safe rule

Loss of plug-in power, firmware failure, watchdog timeout or an unconnected controller must leave the spectrum analyzer usable in its original analog mode.

The original TR1604 achieved this with a physical multi-pole switch. Revision A will preserve that philosophy:

- normally-closed signal relays provide hard X and Y bypass;
- Z defaults to the original blanking path;
- an optional physical BYPASS switch can de-energize all overlay relays;
- fast semiconductor switches may be used inside an enabled overlay cycle, but never as the sole fail-safe path.

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
                +--> comparator/capture                   +<-- overlay blanking
```

## Revision A controller strategy

The first prototype uses the existing STM32F746-based hardware as the UI/controller during development. The internal plug-in board contains the analog acquisition, DAC, switching, protection and power-conditioning circuits. A later compact controller board can replace the development platform without changing the analyzer-side connector.

The original TR1604's 1 MHz timing establishes a useful baseline: a modern converter path at or above 1 MSPS can reproduce the original memory function. Additional margin is desirable for vector characters and short overlay cycles.

## Proposed converters

### Acquisition

- ADS8684A, 16 bit, four bipolar input channels.
- CH1: X input.
- CH2: Y input.
- CH3: Z/blanking observation after conditioning.
- CH4: auxiliary detector or internal calibration channel.

The ADS8684A is suitable for initial acquisition and stored-trace work. Its aggregate sample rate and channel sequencing must be checked against the final simultaneous X/Y capture requirement. If simultaneous aperture is required, Revision B may use separate ADCs or a simultaneous-sampling ADC.

Exact input ranges and filter constants remain provisional until X, Y and Z are measured in the actual analyzer.

### Vector output

Two simultaneously updated DAC channels are required for X and Y. Minimum design targets:

- 16-bit resolution;
- at least 1 MSPS per channel, with a preferred target of 2 MSPS or higher;
- hardware simultaneous update/latch;
- external precision reference;
- output buffers operating from bipolar analog rails;
- independent X/Y gain and offset calibration in firmware, plus hardware trim range.

The final DAC part is intentionally not frozen before voltage and settling measurements.

## Confirmed signal connector P2

The original TR1604 sheet `PM074 1/6` confirms the following 15-position signal connector:

| P2 pin | Label | Direction relative to plug-in |
|---:|---|---|
| 1 | GND | ground/reference |
| 2 | unused on drawing | reserve |
| 3 | `Y_OUT` | output to CRT driver |
| 4 | unused on drawing | reserve |
| 5 | `Y_IN` | input from analyzer |
| 6 | unused on drawing | reserve |
| 7 | `X_OUT` | output to CRT driver |
| 8 | unused on drawing | reserve |
| 9 | `X_IN` | input from analyzer |
| 10 | unused on drawing | reserve |
| 11 | `Z_OUT` | output to CRT driver |
| 12 | unused on drawing | reserve |
| 13 | `Z_IN` | input from analyzer |
| 14 | unused on drawing | reserve |
| 15 | unused on drawing | reserve |

The original drawing writes some internal switched nodes as `X'IN`, `Y'IN`, `X'OUT`, `Y'OUT` and `Z'OUT`; the external connector function remains the six X/Y/Z signal paths above.

## Confirmed ground connector P3

P3 is drawn as a separate multi-position return/ground connector. Pins 1, 3, 5, 7, 9, 11 and 13 are tied to ground in the schematic. The even positions are not shown connected. Connector family and whether these are individual coax shields or cable returns must be verified mechanically.

## Confirmed power connector P1

The original PM074 sheets confirm:

| P1 pin | Rail |
|---:|---|
| 1 | 0 V / GND |
| 2 | +5 V |
| 3 | +15 V |
| 4 | -15 V |

Local decoupling is shown on all three rails. Available current must still be measured or derived from the TR1604 power-supply rating before powering modern digital hardware from these rails.

## Overlay operating modes

1. **Hard bypass** – relays unpowered; original X/Y/Z signals pass through.
2. **Acquire** – original display remains active while X/Y/Z are sampled.
3. **Stored trace** – sampled trace is replayed through X/Y DACs with regenerated Z.
4. **Marker overlay** – short vector marker cycles are inserted between analyzer display cycles.
5. **Menu/vector display** – the CRT is temporarily taken over to draw text or menus.
6. **Tracking measurement** – the stored/reference trace and tracking-generator state are coordinated.

## Important design consequence from the original circuit

The original TR1604 does not merely mix text into an intensity line. It switches the complete X, Y and Z signal set and synthesizes its own X ramp, Y waveform and blanking. The modern plug-in should do the same. Attempting to inject only a Z/video overlay would be less compatible and would not support arbitrary vector text.

## Measurements required before analog schematic freeze

- X input and output DC range, polarity and source impedance.
- Y input and output DC range for 10 dB/div, 5 dB/div and linear modes.
- Z input/output active polarity and voltage levels.
- Sweep period and flyback duration at minimum and maximum scan time.
- Required X/Y settling time and capacitive load at the CRT-driver input.
- Current available from the +15 V, -15 V and +5 V rails.
- Exact P1/P2/P3 connector family, pitch, keying and cable orientation.
- Confirmation that the P3 odd pins are individual signal returns in the actual cable harness.

## Revision A design sheets

1. `01_TR1604_CONNECTORS_AND_BYPASS`
2. `02_POWER_AND_PROTECTION`
3. `03_XY_ACQUISITION_ADS8684A`
4. `04_XY_VECTOR_DAC`
5. `05_XY_FAILSAFE_SWITCHING`
6. `06_Z_BLANKING_INTERFACE`
7. `07_STM32F746_INTERFACE`
8. `08_SD_USB_AND_EXPANSION`
9. `09_TEST_AND_CALIBRATION`

## Non-negotiable constraints

- No connection to the CRT high-voltage section.
- No permanent cutting of original PCB traces.
- Original operation must return automatically when the plug-in is unpowered.
- All analyzer-side signal pins require current limiting and overvoltage protection.
- Analog ground routing and chassis bonding must be documented before PCB release.
- The relay bypass must be verifiable without firmware.
