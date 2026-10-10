# Minimal purchases for this build

The user already has an ELEGOO V4 camera car, UNO Q 2 GB, a USB webcam (assumed to include a microphone), an ELEGOO UNO R3 Super Starter Kit and MAKE electronics parts. Reuse the car's chassis, four motors, battery/charger, sonar, servo/horn and hardware. The exact MAKE package inventory is unspecified; verify actual contents instead of assuming it includes power electronics.

## Buy only if missing

| Quantity | Item | Why / condition |
| --- | --- | --- |
| 1 two-pack | Two L298N boards, [the user's selected product](https://www.amazon.com/dp/B0CR6BX5QL) | Four separate bridge channels; one motor each. Skip if already ordered. |
| 1 | SN74AHCT125 DIP or appropriate breakout | Two 3.3 V → 5 V signal channels for servo/TRIG. Skip only if the exact suitable buffer is already owned. |
| 1 | Q-compatible USB-C host hub with power input | Webcam data plus Q power on its single USB-C port. Reuse a compatible existing hub. Check 5 V power-bank/hub compatibility before buying. |
| 1 | USB 5 V breakout/cable connection for peripheral branch | Only if existing wiring/cables cannot expose a verified 5 V bank output securely. Do not use a higher-voltage PD trigger. |
| As needed | Inline fuse/holder, suitable power wire/connectors, insulation and mounting | Reuse existing supplies where ratings/fit are suitable. Choose fuse from measured load, pack and wire limits; no arbitrary fuse rating is assumed. |

**No additional power converter is required if the existing power bank supports the power plan.** Its model is not known yet: Q requires a 5 V / 3 A-capable feed plus webcam/hub margin, and the servo branch needs adequate additional current. Check simultaneous port limits and transient behavior. A bank that cannot support this needs a different supply arrangement; the code cannot fix inadequate power.

## Reuse kit parts

- Breadboard and jumper wires for low-current signal prototyping, not motor/servo power distribution.
- Four approximately 10 kΩ resistors for enable pull-downs; each board's ENA/ENB gets its own resistor.
- ECHO divider: 10 kΩ + 15 kΩ if available, or two equal resistors in series above and three equal resistors below (e.g. five 1 kΩ resistors). See [WIRING.md](WIRING.md).
- 100 nF capacitor for buffer decoupling; reuse an appropriate kit capacitor if present.
- Normally-open pushbutton for the default D2 software stop. No new NC switch required for this default.
- Battery-box switch if it is accessible and verified to cut both motor supplies with an appropriate current rating.
- Existing bracket materials, screws, standoffs, cable ties and tools.

A separate microphone, new servo, new battery, original R3, shield, ESP camera and line tracker are not required by this build. Upgrade only after an actual compatibility/load problem is demonstrated. The starter kit's small breadboard power module is not the Q power source, and its 74HC595 is not an AHCT buffer.

Use a multimeter you already own or borrow one for polarity/voltage checks. A soldering iron is useful for a secure final installation; a breadboard can be used for initial stationary signal checks. See [commissioning](COMMISSIONING.md).
