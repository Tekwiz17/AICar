# Setup on UNO Q 2 GB

## 1. Prepare the board and peripherals

Install Arduino App Lab using Arduino's [UNO Q getting-started documentation](https://docs.arduino.cc/tutorials/uno-q/user-manual/). Update the board through its supported App Lab flow. This repo targets **Arduino Zephyr core 1.0.0**, **Arduino_RouterBridge 0.4.3** and **Arduino_HardwareServo 0.0.1**, with dependencies pinned in `sketch/sketch.yaml`. An older image/core may need an update before these libraries work.

Check the power bank and hub ratings in [WIRING.md](WIRING.md), then connect the Q-compatible USB-C host hub and webcam. This build expects the webcam's built-in microphone to enumerate as a USB audio input; no separate mic is needed if it does. In normal computer-connected USB device mode the Q cannot simultaneously use the same port as a camera host; use the supported hub/SBC arrangement and App Lab **network mode** for development. The microphone is in the USB webcam; this build does not assume an onboard Q microphone. Power motors off for setup.

Run Arduino's **Hey Arduino!** example and object-detection example separately first. Confirm the microphone hears you and the UVC camera works. The examples and Bricks are listed in [Arduino's App Lab component repositories](https://support.arduino.cc/hc/en-us/articles/24358702846748-Code-repositories-for-Arduino-App-Lab-components).

## 2. Get AICar and its small voice model

On your development machine with Python 3.10 or newer:

```sh
git clone https://github.com/Tekwiz17/AICar.git
cd AICar
python3 scripts/download_voice_model.py
python3 scripts/package_app.py
```

The model comes from [Vosk's official model list](https://alphacephei.com/vosk/models): `vosk-model-small-en-us-0.15`, about 40 MB compressed and roughly 300 MB typical runtime memory. It is Apache-2.0 licensed. The script records the URL and downloaded SHA-256; the record is not a publisher-authenticated hash. The model is excluded from Git but included in the generated import ZIP. Do not replace it with a gigabyte-scale speech model on the 2 GB board.

## 3. Import and inspect the App

Use App Lab's **Import App** flow and choose `build/AICar.zip`. The archive has `app.yaml`, `python/`, and `sketch/` at its root. If the installed App Lab version imposes an archive size limit, copy the same app folder through its supported local/board file workflow instead, including `python/models/`; do not omit the voice model. Confirm the model directory exists at the configured path **inside the Python app**.

Check:

- Both `arduino:object_detection` and `arduino:keyword_spotting` Bricks are included.
- `python/requirements.txt` installs `vosk==0.3.45` in the App environment. Arduino supplies `arduino`, NumPy, Pillow and OpenCV through the normal image. Do not pip-install an unrelated `arduino` package or a second conflicting OpenCV distribution. If Vosk's installed wheel is unavailable on your image's Python/ARM combination, stop and resolve that dependency before enabling movement; do not swap in a cloud recognizer.
- Object Detection uses the default UNO Q lightweight YOLO-X nano model with bounding boxes. A custom centroid-only model is not compatible with this tracker adapter.
- Keyword Spotting uses the default **`hey_arduino`** 16 kHz mono model. A different keyword/model requires changing the voice adapter and sample configuration.
- `sketch/sketch.yaml` contains the UNO Q build profile and the complete library list. App Lab versions may manage libraries through their UI instead of honoring every CLI profile field; add the listed versions there when needed.

`python/config.json` defaults to `usb:0` camera and microphone `"0"`. Use App Lab's Python environment/device tools to list your actual USB peripherals; Linux device numbering can change with plug order. For the mic, Arduino's `ALSAMicrophone.list_devices()` can be used after importing it from `arduino.app_peripherals.microphone`; Select the webcam's audio capture device, not its video device number; these enumerate independently. A stable ALSA name such as `plughw:CARD=YourMic,DEV=0` is preferable once known. Use a current App Lab image with the `Camera("usb:0", ...)` and `Microphone(...)` APIs referenced in [UPSTREAM.md](UPSTREAM.md). Config changes require restarting the app.

## 4. Run with the wheels raised

Follow the new [L298N wiring map](WIRING.md), then [COMMISSIONING.md](COMMISSIONING.md). Remove both boards' ENA/ENB jumpers and regulator-enable jumpers as documented, wire the enable pull-downs, and connect a normally-open pushbutton D2→GND. For an optional NC contact, change `STOP_CONTACT_NC` in the sketch before flashing. Never use the old shield harness with this firmware. Leave motor power disconnected initially. Click **Run** in App Lab to compile/upload the MCU sketch and start Python plus the model services. Only the Q is flashed. The original R3/shield are not connected and no USB-serial control adapter is used. The App monitor should report mode `Stop` and MCU `armed: false`.

If the voice model or any initialization dependency is absent, the app stops with an explicit error and the MCU stays disarmed. If camera or audio processing fails after startup, a fault returns to Stop. The firmware independently stops on a missing control lease.

Once commissioned, say the commands from the README. You can speak continuously, but if one breath is unreliable in a noisy room, say **Hey Arduino**, wait for the monitor's listening message, then say **AutoPilot**, **Object Track**, or **Stop** within four seconds. The car pauses when the wake phrase is recognised. Motor noise affects speech performance, so test Stop while motors run with wheels raised. The physical power cut always remains available.

Object Track: select the mode, hold a distinctive item around the lens centre for the 3-second capture, and wait for a lock. Hold it at the distance you want the car to maintain. Move it farther away to invite following. The car uses apparent size, not learned metric target distance; sonar retains its clearance override. To choose a new item, say Object Track again and repeat capture.

## 5. Keep the 2 GB footprint small

The defaults are a 320×240 camera at 5 FPS, throttled AI inference, a small YOLO model, and a small speech model. No LLM, web video streaming or depth network runs here. Inference and audio run separately from the control heartbeat. The actual total memory, inference rate and stop latency must be measured on your board with camera/mic connected; software tests do not establish a guaranteed 2 GB workload budget. Use `free -h` and the App monitor during commissioning. Close other apps and stop unused examples.

If vision is too slow, the car **holds** when data is stale. Try a smaller supported object-detection model or a lower requested camera rate, then repeat the acceptance checks. Keep the freshness and MCU safeguards; do not increase timeouts merely to make the car move.

## Optional firmware compile on a computer

Install Arduino CLI, then:

```sh
arduino-cli core update-index --additional-urls https://downloads.arduino.cc/packages/package_zephyr_index.json
arduino-cli compile sketch
```

The pinned profile downloads its board core and dependencies. Firmware targets `arduino:zephyr:unoq`; `arduino:avr:uno` is wrong. On Apple Silicon an old Intel-only Arduino `ctags` helper can prevent compilation before code is checked; use a compatible toolchain or the Linux CI job. This is a host-tool issue, not evidence that the sketch compiles. The local verification record documents the native helper used here.

## Power down

Say Stop, confirm `armed: false`, disconnect motor power, stop the app, and shut down Linux through the supported board workflow before removing the Q supply. Do not change the L298N/peripheral wiring while any rail is live.
