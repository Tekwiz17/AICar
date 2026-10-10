# AICar — ELEGOO V4 + Arduino UNO Q (2 GB)

An Arduino App Lab project using **only the Arduino UNO Q**, **two L298N motor-driver modules**, the four original ELEGOO motors, a USB webcam on a pan servo, its built-in microphone, local AI vision, and voice-selected driving modes. The original ultrasonic sensor stays for close-range obstacle protection. **The original UNO R3 and ELEGOO shield are removed.**

Power plan: existing **USB power bank → Q and electronics**, stock **7.4 V / 2000 mAh ELEGOO battery → motors**. No new power converter is mandatory if the bank and hub meet the ratings in the wiring guide; their exact models still need checking. Reuse resistors, a pushbutton and other suitable parts from your starter kits. See the [minimal shopping list](docs/PARTS.md).

**Status:** initial implementation with automated behavior tests and a real UNO Q firmware compile. It has not been run on your physical car. Complete the wiring and commissioning checks before putting its wheels on the floor.

## Modes and voice commands

| Say | Behavior |
| --- | --- |
| **Hey Arduino, AutoPilot** | Drive forward, stop at obstacles, scan left/right while stationary, choose a clearer exit, and make bounded turns. Small occasional heading changes and a repeated-turn stop help avoid continuous circling. |
| **Hey Arduino, Object Track** | Stop for 3 seconds while you place an item near the camera centre, capture its appearance, and follow it. Wait in place if it leaves view, becomes ambiguous, or the path is blocked. |
| **Hey Arduino, Stop** | Disarm the motors. Stay stopped until you explicitly select a mode again. |

The app boots stopped. The official Arduino **Hey Arduino** Keyword Spotting Brick gates a small **offline Vosk** command recognizer. No paid AI service, API key, Wi-Fi connection during driving, or LLM is required; internet is needed for initial installation.

Object Track supports items outside the AI model's named classes through appearance matching. It does **not** guarantee recognition of every possible object or identity: low-texture objects, major viewpoint changes, reflections, lighting changes, and lookalikes can break the lock. Put one distinctive item at the centre; the car captures it once and does not automatically select a replacement. The servo scans during AutoPilot; tracking keeps the camera forward and steers the chassis toward the locked item.

## Read these first

1. [Parts and electrical wiring](docs/WIRING.md) — **exact L298N pins/jumpers, power-bank branches, ECHO divider and physical stop**. Do not use the previous shield wiring.
2. [Install and run with Arduino App Lab](docs/SETUP.md).
3. [Commission and calibrate](docs/COMMISSIONING.md) — wheels raised first.
4. [How the controller works and its limits](docs/ARCHITECTURE.md).
5. [Troubleshooting](docs/TROUBLESHOOTING.md).
6. [Original project and official source references](docs/UPSTREAM.md).

## Hardware retained / removed

Retained: chassis, four motors, ultrasonic sensor, stock battery/charger and a suitable pan servo. Added/reused: UNO Q 2 GB, two L298N boards (one channel per motor; paired left/right commands), USB UVC webcam with Linux-compatible microphone, USB-C host hub, power bank and signal interface parts. Default physical stop is a normally-open kit pushbutton; a normally-closed contact is optional.

Removed from the software and disconnected from the harness: original UNO R3, ELEGOO shield, ESP camera/module, line sensors, IR receiver, RGB effects, original serial JSON protocol, AVR watchdog code, old IMU driving logic, and original battery ADC input. This is a new Linux + Zephyr implementation using the original car hardware and paired-drive convention, with a new L298N pin map. No second controller or USB serial link to an R3 is used.

## Files

```text
app.yaml                     App Lab manifest: object detection + keyword spotting
python/main.py               Camera, AI, voice and Bridge integration
python/config.json           Conservative speeds, thresholds and device settings
python/aicar/control.py      Stop / AutoPilot / ObjectTrack controller
python/aicar/tracking.py     Frozen appearance lock and visual caution zone
python/aicar/voice.py        Shared microphone, wake gate, offline command recognition
sketch/sketch.ino            UNO Q motors, servo, ultrasonic, physical stop and lease
sketch/Safety.h              Independent MCU motion envelope
sketch/L298N.h               Direction, PWM, neutral stop and reversal dead time
sketch/sketch.yaml           Pinned board + library build profile
scripts/download_voice_model.py
python/models/               Local voice model; downloaded separately and ignored by Git
scripts/package_app.py       Build an App Lab import ZIP after model installation
scripts/bench_check.py       Non-driving MCU telemetry / stop check in App Lab
requirements-dev.txt         Dependencies for host behavior tests
.github/workflows/checks.yml Python/C++ checks and UNO Q firmware compile
```

## Local checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=python python -m unittest discover -s tests -v
c++ -std=c++17 tests/safety_test.cpp -o /tmp/aicar-safety && /tmp/aicar-safety
c++ -std=c++17 tests/motor_driver_test.cpp -o /tmp/aicar-motors && /tmp/aicar-motors
arduino-cli compile sketch
```

Install the UNO Q package index as described in the setup guide before compiling. Run-time hardware checks are separate from these software checks.

AutoPilot is **local reactive roaming**, not SLAM or a promise of unique area coverage. Without wheel encoders or a map it cannot prove it has visited somewhere already. Ultrasonic ranging and AI boxes do not detect every hazard, side obstacle, drop-off, glass surface, or table edge. Use a clear, level indoor floor under supervision. The physical motor-power cut remains the reliable emergency stop.
