# TG4132-Pro

Modern internal digital upgrade for the Takeda Riken / Advantest TR4132 and TR4132N spectrum analyzer.

## First hardware target

A reversible **TR1604-compatible X/Y/Z plug-in module** that sits between the analyzer and CRT driver. The first revision focuses on:

- transparent fail-safe pass-through of the original X, Y and Z signals;
- acquisition of the original sweep and amplitude signals;
- digitally generated vector overlay on the original CRT;
- SD storage and USB keyboard/control support;
- an expansion interface for the later tracking-generator RF board.

Development branch: `feature/tr1604-plugin`.

See [`docs/hardware/TR1604_PLUGIN_ARCHITECTURE.md`](docs/hardware/TR1604_PLUGIN_ARCHITECTURE.md).
