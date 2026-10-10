# Commissioning — complete on the actual car

No physical-board measurements were available when this project was written. Record your board/image versions, L298N module revision/labels, camera/microphone models and measurements in a local copy of this checklist.

## 1. Unpowered inspection

- Remove/disconnect the old UNO, ELEGOO shield, ESP camera, line tracker, IR/RGB/IMU and battery-ADC signal.
- Verify the exact new D4–D9 L298N signal map in WIRING.md, one module per side and one output channel per motor.
- Remove ENA/ENB jumpers on both modules and fit a pull-down at each enable. Remove regulator-enable jumpers and verify externally supplied logic 5 V is an input.
- Check polarity, fuse, motor-power disconnect, common ground, and correct separation of battery motor supply and bank electronics supply.
- Check each AHCT channel, OE, decoupling connection.
- Check echo divider and confirm there is no parallel raw-echo connection.
- Mount camera and sonar together. Check centre alignment, servo torque and cable clearance.

## 2. Power and logic with motor power disabled

Have a meter and, for PWM/echo, preferably an oscilloscope or logic analyzer.

- Verify Q power is stable with camera/mic and AI active; check actual total current against the source/hub rating.
- Verify bank simultaneous-port ratings and voltage stability with Q AI/camera active and servo moving. Connecting peripheral USB power must not reset the Q.
- Verify both L298N logic 5 V inputs and the servo supply before inserting signal leads. Do not use onboard driver regulators for Q or servo.
- Measure echo after the divider at approximately 3 V peak for a 5 V source; check for overvoltage and unintended backfeeding.
- Confirm all four enables are LOW while Q resets, app is absent, app is stopped and firmware is initially booted. A remaining enable jumper is a failed check.
- Verify the default pushbutton reads HIGH released and LOW pressed. Pressing must prevent arming. In optional NC mode only, released is LOW and pressed/unplugged is HIGH. Verify the motor-power switch independently disconnects both driver motor supplies.
- Run `scripts/bench_check.py` inside the App Lab Python environment, or temporarily use its body in a separate disarmed app. It never arms or moves motors. Do not run a competing Bridge controller while AICar is driving.
- Check distance against a flat board at 200, 350 and 1000 mm. Remove the sonar: `distance_mm` must become -1 / unavailable. Timeouts must never become a 4000 mm “clear” reading.

## 3. Wheels raised — powered motor checks

Secure the chassis so no wheel can touch a person, table, cable or loose object. Keep the physical motor-power disconnect in reach. Use a stationary flat board roughly 1 metre ahead for valid sonar. Use the normal voice commands rather than bypassing the firmware envelope.

- Say Hey Arduino, AutoPilot. Confirm both motor pairs drive forward with a clear path. Wrong polarity: power off and fix individual motor leads or entire-side polarity constants. Verify every wheel points forward, since mirrored mounting can reverse one motor.
- Introduce a flat obstacle at 350 mm. Translation must stop. Scans occur only with wheels stationary; verify 125° actually faces left, 55° right, and 90° forward. Swap the left/right config angles if needed.
- Check bounded left and right pivots; the sign convention is positive left / negative right for a right turn. No full reverse command is accepted.
- Say Hey Arduino, Stop with motors running. The mode must stay stopped through target/camera activity. Test noise and microphone placement; do not rely on speech as the emergency power cut.
- Press the kit stop button while running. Motors must stop/disarm; release must not resume. In optional NC mode, also unplug the contact and verify stopping. An unplugged default normally-open button is NOT detected. Select a new mode only after correcting the cause.
- Check driver temperature, individual motor current and coast stopping distance. The L298N chip's current limit is not a promise that these modules support a motor's stall load.
- Use the independent rated power switch: motors must lose power even if software is unresponsive.

## 4. Failure injection

Measure behavior, not just log messages. Record observed stop latency using video or electrical traces.

| Test | Expected |
| --- | --- |
| Stop/kill the Python app while moving | MCU disarms after its 500 ms lease plus bounded ping/loop/scheduling overhead |
| Disconnect camera / stall inference | Freshness expires and motion holds; fatal camera error requests Stop |
| Disconnect microphone | Audio freshness/worker fault requests Stop; movement does not continue indefinitely |
| Remove sonar / obstruct echo | Unknown/stale range prohibits motion, even if camera sees a target |
| Pan away from forward | No motor motion during panning or settling |
| Break Bridge connectivity | Host requests Stop when possible; MCU lease expires independently |
| Release emergency stop | No automatic rearm |
| Reset Q while L298N modules remain powered | Enable pull-downs keep all four channels disabled during startup; verify physically |

A firmware hang is outside the command-lease mechanism. Demonstrate that the physical motor-power cut works independently; software tests cannot prove this hardware function.

## 5. Object Track tests

- Place one distinctive, textured item centred and relatively small in the frame. Select Object Track and hold it still for at least the 3-second capture plus three matched frames.
- Check it holds at the captured distance. Move the item farther away: the car should follow slowly. Move it toward the lens: hold, not reverse.
- Move the item left/right: verify chassis steering direction.
- Remove the item: both sides stop and the camera remains forward. Return it: after confident matches it can resume following.
- Present two visually identical items: verify ambiguous matching holds. This is conservative matching, not guaranteed individual identity recognition.
- Put a separate obstacle between car and target: sonar override stops motion. Use a large recognised object to test the visual caution rule independently with a distant sonar reflector.
- Test low-texture and rotated subjects: failure should cause waiting or an explicit failed-capture stop, not selection of another target.

## 6. Floor trial

Use a level open indoor floor, low speed, no stairs/table edges, and a person supervising with the power switch. Check braking distance at the configured PWM with the actual battery charge, load and floor. Increase obstacle distance if stopping margin is small; do not reduce the firmware's distance floor.

Observe AutoPilot in a simple obstacle arrangement. It should stop before scans, turn briefly, then prefer forward progress. A cramped or repetitive layout should trigger a stuck stop, not endless circles. Do not expect full room coverage. If timed pivots are erratic, correct traction/polarity/mechanics or add encoders.

## 7. Acceptance record

Record:

- Q image, App Lab/Python/Brick/core/library versions;
- L298N module revision/labels and verified input/power labels;
- power bank/hub model and simultaneous-port ratings;
- camera and built-in microphone device names;
- measured Q+peripheral current, motor current/driver temperature and peak echo voltage;
- forward PWM, motor polarity, physical servo angles;
- memory available with both AI services and Vosk loaded;
- capture/inference latency and observed software/physical stop latency;
- every failure-injection result, target-loss result, and floor-trial result.

Only after these checks pass can this particular hardware assembly be described as tested. Automated CI cannot replace them.
