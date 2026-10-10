# Troubleshooting

| Symptom / monitor reason | Check |
| --- | --- |
| Cannot import/start | Manifest at ZIP root; complete model folder; required App Lab Bricks and versions |
| Missing Vosk model | Run download then packaging scripts; `python/models/` must be inside imported app |
| Missing `vosk`, `cv2`, or Arduino modules | App Lab requirements installation and board image. Host behavior-test environment is separate from board app environment |
| No camera / microphone | Powered USB host hub, correct source config, competing examples stopped, Linux UVC/ALSA compatibility |
| Wake detected but command ignored | Say command within four seconds; read monitor; use exact AutoPilot/Object Track/Stop grammar; reduce motor noise |
| One-breath command intermittent | Pause after Hey Arduino; wake and recognizer latency differ |
| App refuses to arm | Default pushbutton must leave D2 HIGH released and pull it LOW pressed; verify `STOP_CONTACT_NC` matches your wiring; servo attach must succeed; correct UNO Q core and HardwareServo library |
| `waiting for fresh AI vision` | Model service not ready/too slow or old captured images. Check RAM/load; no other running examples; retain timeouts |
| `waiting for forward range` | Sonar timeout/no echo, incorrect divider/pins, narrow/angled surfaces, servo not centred/settled |
| Scan never succeeds | Camera and sonar must share mount; swapped scan angles; flat reflectors; side ranges >450 mm; fresh angle-matched AI result required |
| Stops close to obstacle and cannot turn | MCU pivot margin is 180 mm; no blind reversing. Stop, move car manually, select mode again |
| Moves backward/spins on a clear path | Raise chassis and verify every motor's lead polarity and L298N input map; check left/right direction constants |
| Motors run at boot or speed ignores PWM | Immediately cut motor power; remove ENA/ENB jumpers, verify pull-downs and PWM wiring |
| One wheel reverses relative to its side | Power off and swap that motor's two output leads; do not join outputs |
| Drivers hot / car slower than original | L298N voltage loss and module thermal limits; measure current, check load; do not raise PWM blindly |
| Servo resets Q / bank turns off | Bank current sharing, low-load auto-off, servo stall/current path; verify the separate peripheral output |
| Button unplugged but no stop | Expected in default normally-open mode; optional NC mode requires the matching contact and sketch setting |
| Target capture fails | Use a distinctive textured item, stable lighting and uncluttered centre; blank/shiny items may not form a usable template |
| Target returns but won't reacquire | It must resemble the frozen template and be within tested scale range; after major rotation say Object Track again |
| Stop works only in a quiet room | Relocate/isolate mic from motor/servo vibration and wind; lower speed; test noise. Use the physical power cut |
| MCU `command_timeout` | App heartbeat/RPC is late or disconnected; do not extend lease to mask it. Fix load/Bridge and select mode again |
| Q reboots under load | Check bank simultaneous-port limits, hub compatibility, separate servo wiring/returns and cable voltage sag; no driver regulator feeds the Q |
| CLI missing `Arduino_RPClite.h` | Use complete `sketch/sketch.yaml` profile, including transitive libraries, not only RouterBridge |
| Mac `bad CPU type` in `ctags` | Native compatible Arduino helper/toolchain or Linux firmware CI required; do not claim build success from behavior tests |

Start with motors disconnected. Check both L298N boards' power inputs and jumpers before chasing software errors. Do not troubleshoot live mechanical motion by raising the speed or loosening safety thresholds.
