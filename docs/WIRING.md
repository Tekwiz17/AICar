# Wiring and parts

## Before connecting the old shield

The original ELEGOO sketch was written for a 5 V AVR UNO. The UNO Q's ordinary Arduino GPIO headers use **3.3 V signals**. Treat the old shield as a 5 V device until its specific revision is inspected. **Use a harness, not a full header stack.** Mechanical UNO compatibility does not establish electrical compatibility.

The upstream pin map is verified from `DeviceDriverSet.h` and `DeviceDriverSet.cpp`; the shield's component part numbers, regulator topology, connector pin order and exact PCB revision still need physical verification. Do not infer them from wire colours. If your shield differs from that map, stop and compare its schematic/labels before wiring.

## Parts

| Part | Requirement |
| --- | --- |
| UNO Q | 2 GB RAM model; not the original UNO / R4 / VENTUNO Q |
| Camera | Linux-compatible USB UVC camera, small enough for the servo mount; 320×240 or 640×480 support |
| Microphone | USB audio input with 16 kHz mono capture supported by ALSA; camera-integrated mic can work if enumerated separately |
| USB hub | USB-C host hub with USB-A data ports and a power-input arrangement compatible with UNO Q; board requires 5 V / 3 A, plus peripheral budget |
| Output level shifters | Two **74AHCT125** packages at the shield's regulated 5 V logic rail: seven unidirectional channels, 3.3 V input → 5 V output. Use AHCT, not HC; generic I²C MOSFET boards are unsuitable for PWM. Verify the selected manufacturer's thresholds. |
| Echo divider | 10 kΩ upper resistor and 15 kΩ lower resistor, 1% recommended; 5 V becomes about 3.0 V |
| Servo supply | Separate regulated 5 V supply sized for the actual servo's stall current; often at least 2 A for a small servo. Keep its positive rail isolated from the Q and shield regulators. |
| Emergency switch | Normally-closed contact for D2 input; a separate suitably rated contact/switch physically disconnects motor battery power. Use a fuse appropriate to the pack and motor wiring. |
| Other | Interface perfboard, 100 nF decoupling per AHCT package, 10 kΩ input pull-downs, wiring, strain relief, camera/sonar bracket |

A hub that requires higher PD voltage may not suit this board. The Q requests 5 V; confirm the power arrangement with the hub manufacturer. Do not power motors or a servo from the Q's USB/GPIO header rail.

## Power topology

```text
Q-compatible 5 V / 3 A source (+ USB peripheral margin)
   -> powered USB-C host arrangement -> UNO Q
                                   -> UVC camera + USB microphone

Original motor battery -> fuse -> physical motor-power switch -> ELEGOO shield motor supply
                                                              -> four original motors
Shield's VERIFIED regulated 5 V LOGIC output -> AHCT VCC / retained sonar
Separate regulated servo 5 V -> servo positive wire ONLY

Q GND ---- interface GND ---- shield GND ---- sonar GND ---- servo supply GND
```

Keep **Q 5 V, Q VIN, Q 3.3 V, Q RESET, shield VIN and shield 5 V power header pins isolated from each other**. Only ground and the listed interface signals cross the harness. Do not inject a second regulator into the shield's existing 5 V rail. Verify its logic supply with a meter and the board documentation; if it is not usable without the original UNO, provide a validated power solution for that revision before proceeding. Use proper battery protection; the old pack is not assumed to be sufficient for Q + camera + servo.

Mount and power off all systems before changing wires. Avoid leaving a powered 5 V echo feeding an unpowered Q through its input protection. Switch off the sensor/shield and Q together, or use a proper 3.3 V buffer with 5 V-tolerant input and power-off isolation (Ioff), validated for the chosen part, instead of the divider.

## Signal harness

| UNO Q pin | Interface | Shield / peripheral connection |
| --- | --- | --- |
| D5 | AHCT output channel | Shield D5, right-side motor PWM |
| D6 | AHCT output channel | Shield D6, left-side motor PWM |
| D7 | AHCT output channel | Shield D7, right-side direction |
| D8 | AHCT output channel | Shield D8, left-side direction |
| D3 | AHCT output channel | Shield D3, motor standby/enable |
| D10 | AHCT output channel | Pan servo signal, formerly shield D10/Z; servo positive uses separate supply |
| D13 | AHCT output channel | Ultrasonic TRIG, formerly shield D13 |
| D12 | Divider or validated isolated buffer | Ultrasonic ECHO, formerly shield D12 |
| D2 | Direct to **separate NC switch** and GND | Emergency-stop input; released contact closes D2 to GND; opening/pressing/unplugging stops |
| GND | Common reference | Shield, translator, sonar, servo supply ground |

Disconnect the shield's stock D2 button from this interface: a normal pushbutton is not the NC safety contact. Leave A0–A5, D0/D1, D4, D9, D11, I²C, RESET and all unlisted shield signals disconnected from the Q. Remove the ESP module, line tracker, IR, IMU and RGB peripherals from the harness. Do not expose the shield's old battery ADC signal on A3 to the Q.

### AHCT125 wiring

Each output signal uses one A→Y channel. Q pin → A input; Y output → shield/peripheral signal. Connect package VCC to verified shield 5 V logic, GND to common ground, active-low OE to GND. Add 100 nF between VCC and GND close to each package. Add a 10 kΩ pull-down on each A input, especially standby, so a floating Q pin at reset does not enable motors. Ground unused inputs and disable unused outputs. Follow the manufacturer's **actual package pinout**, including OE pins; this guide names functions rather than guessing IC lead numbers.

Verify D3 at the shield is LOW before MCU startup. A logic switch alone is not a guaranteed emergency power cut; the rated motor-supply disconnect is separate.

### Echo divider

```text
HC-SR04 ECHO / shield D12 ---- 10 kΩ ----+---- Q D12
                                       |
                                     15 kΩ
                                       |
                                      GND
```

Never connect the shield's raw echo to Q D12 in parallel with the divider. At 5.0 V the divider output is 3.0 V; check the actual supply and measured peak. Q D13 is level-shifted to 5 V TRIG. Use common ground.

## Motors and servo

The original four motors remain plugged into the original shield. Two motors on each side are one control channel; four independent speed channels are not available. Forward uses HIGH on both direction pins in the original source. Commission with the chassis raised. If one side turns backward, adjust `LEFT_FORWARD_HIGH` / `RIGHT_FORWARD_HIGH` in the sketch or correct that side's motor wiring with power off.

Attach the camera **and sonar** to one rigid pan bracket, pointed in the same horizontal direction. The servo is 90° forward, nominally 125° left and 55° right. A shared mount lets stationary sonar scans measure where the camera looks. Secure the USB cable so it neither loads the horn nor catches a wheel. Use a stronger servo if the original microservo cannot hold the camera steadily.

Firmware uses conservative 1000–2000 µs servo endpoints, not the original wide 500–2400 µs setting. Calibrate the horn physically at 90°. If angle direction is reversed, swap `servo_left` and `servo_right` in `python/config.json`; keep centre at 90. Keep all scan angles within 55–125. This code has no tilt servo.

## Electrical verification still required

Confirm the shield revision, power input labels, logic-rail availability, motor polarity, battery condition, servo current, USB power budget and each measured signal before assembly. The repo cannot verify your particular physical shield from the upstream C++ files alone. See [commissioning](COMMISSIONING.md) for the controlled bring-up sequence.
