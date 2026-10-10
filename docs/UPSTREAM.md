# Sources, provenance and licensing

Research checked 2026-10-10. API/board support can evolve; the physical L298N boards, power bank and USB hub still need inspection.

## ELEGOO reference

[Original ELEGOO Smart Robot Car Kit V4.0 New repository](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0-New), examined at commit **76d82704b20b8b38d3eb874afd865b349cbc1a48**.

- [`DeviceDriverSet.h`](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0-New/blob/76d82704b20b8b38d3eb874afd865b349cbc1a48/DeviceDriverSet.h): motor PWM D5/D6, direction D7/D8, standby D3, sonar D13/D12, servo Z D10.
- [`DeviceDriverSet.cpp`](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0-New/blob/76d82704b20b8b38d3eb874afd865b349cbc1a48/DeviceDriverSet.cpp): HIGH/LOW direction control and standby behavior.
- [`MotionControl.cpp`](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0-New/blob/76d82704b20b8b38d3eb874afd865b349cbc1a48/MotionControl.cpp): paired left/right motor convention.

The upstream snapshot has no top-level license granting wholesale redistribution. This repo does not vendor its AVR implementation or bundled third-party headers. It contains newly written software referencing the original paired-drive behavior and retained servo/sonar pins. The current motor interface is the new L298N map in WIRING.md; shield standby D3 is not used. Ownership/licensing of the original ELEGOO code is not claimed here.

## Official Arduino sources

- [UNO Q manual/datasheet](https://docs.arduino.cc/resources/datasheets/ABX00162-ABX00173-datasheet.pdf): dual Linux/MCU architecture, 2 GB variant, 3.3 V MCU headers, USB host/power requirements. This is UNO Q, not VENTUNO Q.
- [UNO Q user manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/): setup and network/SBC workflow.
- [App Lab examples](https://docs.arduino.cc/software/app-lab/tutorials/examples/) and [component repositories](https://support.arduino.cc/hc/en-us/articles/24358702846748-Code-repositories-for-Arduino-App-Lab-components).
- [App Bricks Python](https://github.com/arduino/app-bricks-py), inspected at **96521e1cd33b1811b527686dfa7379342dbf8c45**: ObjectDetection, model dimensions, percent confidence / input-pixel boxes, Camera, Microphone, KeywordSpotting, Bridge RPC and App lifecycle.
- [Object Detection API](https://github.com/arduino/app-bricks-py/blob/96521e1cd33b1811b527686dfa7379342dbf8c45/src/arduino/app_bricks/object_detection/__init__.py): `detect(PIL.Image)`, `get_model_info()`, bounding boxes.
- [Keyword Spotting API](https://github.com/arduino/app-bricks-py/blob/96521e1cd33b1811b527686dfa7379342dbf8c45/src/arduino/app_bricks/keyword_spotting/__init__.py): custom microphone adapter and `on_detect("hey_arduino", callback)`.
- [App examples source](https://github.com/arduino/app-bricks-examples): App manifest, Python/sketch directories and `App.run(user_loop=...)` pattern.
- [Arduino Router Bridge](https://github.com/arduino-libraries/Arduino_RouterBridge): `Bridge.begin`, `Bridge.provide`, typed arguments / String response.
- [Arduino HardwareServo](https://github.com/arduino-libraries/Arduino_HardwareServo): UNO Q hardware PWM servo support; D10 uses a different timer from motor PWM D5/D6. The old AVR Servo implementation is not reused.
- [Arduino Zephyr core](https://github.com/arduino/ArduinoCore-zephyr): UNO Q pin/timer support and board profile.

No Arduino library source is copied into this repo. App Lab and CLI obtain dependencies separately with their respective licenses.

## Speech and image dependencies

[Vosk models](https://alphacephei.com/vosk/models) and [Vosk API](https://github.com/alphacep/vosk-api): small English model and grammar-limited offline recognition. Model `vosk-model-small-en-us-0.15` and Vosk API are Apache-2.0. Downloaded model/license files remain in its folder and are included in a local App ZIP.

OpenCV and NumPy/Pillow are provided by the App Lab environment. Test dependencies are installed separately. The default Arduino model services distribute their own model artifacts and licenses; this repository does not embed them. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Current hardware sources

- [ST L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf): separate direction/enable inputs, 2.3 V minimum HIGH, logic 5 V supply, output-current and saturation-voltage specifications. Third-party board jumper/regulator behavior must still be verified.
- [User-selected L298N two-pack](https://www.amazon.com/dp/B0CR6BX5QL): WWZMDiB, ASIN B0CR6BX5QL, resolved from https://a.co/d/00UPOao3.
- [TI SN74AHCT125 datasheet](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf): 5 V buffer with TTL-compatible inputs and package pinout.
- [ELEGOO V4 product specifications](https://eu.elegoo.com/products/elegoo-smart-robot-car-kit-v-4-0): 7.4 V, 2000 mAh lithium pack, 7.2–8.4 V listed operation, USB charging/protection; no published maximum discharge current or protection thresholds found.
- [ELEGOO UNO R3 Super Starter Kit](https://us.elegoo.com/products/elegoo-uno-r3-super-starter-kit): reusable resistors, pushbuttons, breadboard and jumper wires. Check actual kit revision/contents; MAKE package contents are not assumed.
