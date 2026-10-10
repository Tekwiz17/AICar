# Software validation record

Checked locally on 2026-10-10. This record concerns software only; it is not a physical-car acceptance record.

## Firmware

The current **UNO Q + two L298N modules** sketch compiled with **Arduino CLI 1.5.1**, **arduino:zephyr:unoq / core 1.0.0**, **Arduino_RouterBridge 0.4.3**, **Arduino_HardwareServo 0.0.1**, and the pinned transitive dependencies in `sketch/sketch.yaml`.

Reported sizes:

- program storage: **101,744 / 786,432 bytes (12%)**;
- global-variable memory: **41,152 / 262,144 bytes (15%)**.

These numbers concern the MCU sketch, not Linux RAM or AI model memory.

This Mac's downloaded Arduino `ctags` helper was x86_64 and could not execute. For local compilation only, Arduino's ctags source was built as a native arm64 temporary helper (renaming its reserved `__unused__` macro to avoid collision with the macOS SDK). `tools.ctags.path` was overridden on the compile command. Project firmware was not weakened or replaced by stub headers to get this result. The Linux CI job uses the normal Arduino toolchain.

## Host checks

**21 Python tests passed**, and both host C++ safety and L298N motor-driver executables passed. The test suite exercises Stop latching, stale vision/range, missing echo, emergency stop/disarm, bounded scan/turn sequencing, repeated-turn escape, target loss/reacquisition, lookalike ambiguity, bounding-box scaling, AI caution, wake gating, shared microphone capture, and the production runtime's mode/Bridge/fault integration using fake hardware. Separate C++ executables directly test `Safety.h` and the production `L298N.h` driver using injected pin I/O. Driver checks cover disabled startup, forward/reverse direction levels, PWM magnitude, disable-before-reversal with 200 µs dead time, neutral stop, invalid PWM rejection, reversed mounting polarity, and default normally-open / optional NC stop polarity.

A Linux ARM64 `vosk==0.3.45` wheel was successfully downloaded for dependency compatibility; its engine was not executed on this Mac. The official small model was downloaded and unpacked successfully.

The App Lab manifest, sketch profile and CI YAML were parsed. The new header is included in the generated App Lab import package; the ZIP contains no AVR firmware or R3 serial transport. Python sources were syntax-compiled. An App import ZIP was generated and its required entries checked. The model downloader is kept separate from Git; a full local package requires the downloaded voice model.

## Not yet verified

Actual L298N module jumper/regulator arrangements, motor current/driver temperature, logic and supply voltages, motor polarity, power-bank simultaneous-port ratings/auto-off, USB host/hub behavior, actual webcam video/audio drivers, complete App Lab container deployment on the board, full AI+voice RAM footprint on 2 GB, inference frame rate, real microphone command accuracy, servo load/angles, stopping distances/latencies, and behavior on a physical floor.

Complete [COMMISSIONING.md](COMMISSIONING.md) and record those results before describing the robot as hardware tested. The code has no guarantee of arbitrary object identity, collision-free navigation, or full room coverage.
