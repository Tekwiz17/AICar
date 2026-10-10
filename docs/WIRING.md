# Wiring: UNO Q + two L298N modules

This build uses **only the UNO Q**, with two external L298N boards and four original motors. Remove the original UNO R3 and ELEGOO shield. The previous shield harness is incompatible with this sketch. The Q's Linux side runs vision/voice; its own microcontroller controls the motors, servo and ultrasonic sensor through Bridge.

## Power without buying a converter

The preferred low-purchase option uses the existing **USB power bank for electronics** and the **stock ELEGOO battery for motors**. No additional converter is required if the bank's ports, combined output rating and hub support the arrangement below. The bank model/output ratings are not yet known, so this is a connection plan, not a claim that the user's particular bank is compatible.

```text
USB power bank
  |-- 5 V / 3 A-capable USB-C output
  |       -> compatible hub POWER INPUT -> hub HOST cable -> Q USB-C
  |                                           USB data port -> webcam with microphone
  |
  `-- separate regulated 5 V output and verified USB-to-wire connection
          -> servo positive, sonar VCC, AHCT buffer VCC
          -> BOTH L298N logic 5 V inputs (regulator jumpers removed)

ELEGOO 7.4 V battery -> fuse -> accessible motor-power disconnect
                             -> BOTH L298N motor-supply terminals

Q GND -- bank peripheral-output GND -- both L298N GND
      -- battery negative -- sonar GND -- servo GND -- buffer GND
```

The Q source/cable must provide **5 V at 3 A**, with allowance for the webcam/hub. The additional 5 V output must support servo startup/stall plus sensor/driver-logic load; allow at least 2 A for the original small servo branch until its actual load is measured. Verify the bank's **simultaneous-port** ratings: plugging in a second cable can reduce output or reset the first port. Avoid low-current auto-off and confirm operation with the Q booting and AI running. Do not assume a bank's headline wattage establishes either requirement.

A hub needs USB host data and a power-input arrangement that works with the Q's **5 V-only PD request**. Ordinary charge-only splitters do not supply camera data. Do not connect a higher-voltage PD trigger to the Q or servo. A second USB output can be exposed with a suitable breakout or an existing USB cable prepared and insulated by someone comfortable with wiring; identify polarity with a meter, not cable colours. Keep high-current motor and servo connections off the solderless breadboard and Dupont signal wires.

**Positive supply connections:** battery positive goes only to driver motor supply. Peripheral 5 V goes only to servo, sensor, buffer and driver logic. Do not connect it to Q 5 V/VIN as an additional feed in this USB-powered arrangement. Outputs on the same bank may internally share a supply, but never tie separate output-positive wires together externally. All grounds share a reference. Motor/servo current returns go directly to their sources, not through Q ground pins or the signal breadboard.

The stock pack is advertised as 7.4 V, 2000 mAh (14.8 Wh nominal), USB rechargeable with protection circuitry; ELEGOO lists 7.2–8.4 V operation. Its discharge-current rating and protection thresholds are unpublished in the cited page. Reusing it for the original four motors avoids assuming it can also support Q load. Keep its original charger/protection and verify battery condition/current capability; the new firmware has no battery-voltage monitoring because the shield's ADC connection is removed. Stop and recharge before the pack is exhausted; do not rely on an unspecified protection threshold as routine charge management.

Direct pack-to-Q VIN is not the default: VIN requires 7–24 V and pack voltage can sag/drop below 7 V. If the power bank does not meet requirements, change the power arrangement before driving; do not replace regulation with resistors or use an L298N's small regulator for Q/servo power. A suitable regulated source is an alternative, not a mandatory new purchase when the bank works.

## L298N board jumpers and motors

Use the linked [WWZMDiB two-pack, ASIN B0CR6BX5QL](https://www.amazon.com/dp/B0CR6BX5QL), or electrically equivalent modules whose labels/schematic you verify. Module layouts vary; the ST chip datasheet does not document every third-party board's regulator arrangement.

1. Remove **ENA and ENB jumpers on both boards**. These jumpers normally tie enable HIGH and would defeat startup disable/PWM control.
2. Remove each board's **5V-EN / regulator-enable jumper** and verify its 5 V terminal becomes a logic **input**. Feed both from the peripheral 5 V source. Never join regulator outputs or drive a live regulator output with external 5 V. If its jumper function is undocumented, identify it before connecting power.
3. Connect pack supply to the motor terminal often marked `12V`, `VS` or `+`; the label `12V` does not mean you must supply 12 V. Connect ground as above.
4. Board LEFT: front-left motor to OUT1/OUT2; rear-left to OUT3/OUT4. Board RIGHT: front-right to OUT1/OUT2; rear-right to OUT3/OUT4. **One motor per bridge channel. Do not join output channels together.**
5. At each of the four enable inputs, fit a roughly **10 kΩ pull-down to GND**, physically near the module. Reuse kit resistors. These keep the motors disabled while the Q boots/resets or a signal lead disconnects.

The L298N accepts Q 3.3 V input/enable signals directly (chip minimum HIGH is 2.3 V); no level shifter is needed for its control inputs. Its 2 A/channel DC figure is an absolute chip limit, not a guaranteed continuous module rating. Check each motor's startup/stall current and heatsink temperature. It loses substantial motor voltage as heat (chip total drop typically 1.8 V at 1 A, up to 3.2 V at that current), so speed and battery runtime can be worse than the original TB6612 shield. Do not compensate by blindly raising PWM or supply voltage.

## Exact signal map

The two channels on each board share input commands; they still have separate motor outputs.

| Q pin | Connect to |
| --- | --- |
| **D6** | LEFT board ENA **and** ENB |
| **D8** | LEFT board IN1 **and** IN3 |
| **D9** | LEFT board IN2 **and** IN4 |
| **D5** | RIGHT board ENA **and** ENB |
| **D7** | RIGHT board IN1 **and** IN3 |
| **D4** | RIGHT board IN2 **and** IN4 |
| **D10** | AHCT input → pan servo signal |
| **D13** | AHCT input → ultrasonic TRIG |
| **D12** | Reduced ultrasonic ECHO via divider below |
| **D2** | Normally-open kit pushbutton to GND: pressed LOW = stop |
| **GND** | Common ground network described above |

D3 is unused: there is **no shield standby pin** in this build. Leave D0/D1, D3, D11, A0–A5, RESET and other unlisted Q signals unconnected. Disconnect the ESP camera, line tracker, IR, RGB, IMU and old battery ADC wiring. Do not plug a motor, servo power wire or raw pack voltage into a Q signal pin.

Forward defaults to IN1/IN3 HIGH, IN2/IN4 LOW on both boards. The mirrored physical motors may need individual lead swaps: with power off, reverse only the wrong motor's two leads. For an entire side reversed, change `LEFT_FORWARD_HIGH` or `RIGHT_FORWARD_HIGH` in `sketch/sketch.ino`. Verify all four wheels, not just one on each side. Direction reversals disable that side's PWM and insert 200 µs dead time first. Zero commands disable enables and make both direction inputs LOW; stopping is a coast, so measure real stopping distance.

## Servo and ultrasonic logic

Use one **74AHCT125** at peripheral 5 V for two output signals: Q D10 → servo signal; Q D13 → sonar TRIG. AHCT accepts 3.3 V inputs at a 5 V supply. The kit's 74HC595 is a different chip; do not substitute it or a generic bidirectional I²C shifter.

For a standard **14-pin SN74AHCT125 DIP**, after verifying its datasheet/orientation:

- VCC pin 14 → peripheral 5 V; GND pin 7 → common ground; 100 nF capacitor between them nearby.
- Servo: Q D10 → 1A pin 2; 1Y pin 3 → servo signal; active-low 1OE pin 1 → GND.
- TRIG: Q D13 → 2A pin 5; 2Y pin 6 → sonar TRIG; 2OE pin 4 → GND.
- Unused inputs pins 9 and 12 → GND; unused OEs pins 10 and 13 → 5 V; unused outputs unconnected.
- Servo positive and sonar VCC → peripheral 5 V; their grounds → common ground.

A breakout may already include decoupling and OE wiring; check its labels. Power Q and this peripheral branch together: do not leave signals feeding unpowered devices. Disconnect all supplies before changing wiring.

### ECHO divider using resistors you already have

The project conservatively reduces the sonar's 5 V ECHO to about 3 V, without relying on conditional 5 V-tolerant pin modes. No special ECHO converter board is required.

```text
Sensor ECHO --- upper resistance ---+--- Q D12
                                   |
                             lower resistance
                                   |
                                  GND
```

Use either **upper 10 kΩ / lower 15 kΩ**, or kit resistors in series: **upper two 1 kΩ resistors (2 kΩ total), lower three 1 kΩ resistors (3 kΩ total)**. Both give 0.6 × input voltage, about 3 V from 5 V. Two and three equal 10 kΩ resistors work too. Verify values with a meter. Do not connect raw ECHO directly in parallel. Resistors are suitable for this signal, not for powering the Q or servo.

## Physical stop and mounting

Reuse a kit normally-open pushbutton between D2 and GND. The sketch uses INPUT_PULLUP: pressing stops/disarms; releasing does not restart. This input **cannot detect an unplugged button**. Use diagonally opposite/contact-pair legs on four-leg buttons and check continuity before connecting.

An optional normally-closed stop contact can detect an open/disconnected wire: set `STOP_CONTACT_NC = true` in the sketch and reflash; closed-to-GND means released, opening means stop. Do not mix these two wiring modes. Neither input is a certified emergency stop; keep an accessible, suitably rated battery disconnect that cuts both boards' motor supply independently of software. The stock battery-box switch can serve only if verified to interrupt that supply and be adequately rated.

Mount **camera and sonar together** on the pan bracket. Centre is 90°, nominal left 125°, right 55°; servo pulse endpoints are 1000–2000 µs. Reuse the original SG90 if it holds the camera and cable steadily. Make a lightweight bracket from existing materials; a stronger servo is optional only after testing load. Swap left/right config angles if mounting reverses their direction. Prevent the USB cable catching wheels or pulling the horn.

See [minimal purchases](PARTS.md), [setup](SETUP.md) and [commissioning](COMMISSIONING.md) before floor trials.
