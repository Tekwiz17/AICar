# Troubleshooting

| Symptom / monitor reason | Check |
| --- | --- |
| Cannot import/start | Manifest at ZIP root; complete model folder; required App Lab Bricks and versions |
| Missing Vosk model | Run download then packaging scripts; `python/models/` must be inside imported app |
| Missing `vosk`, `cv2`, or Arduino modules | App Lab requirements installation and board image. Host behavior-test environment is separate from board app environment |
| No camera / microphone | Powered USB host hub, correct source config, competing examples stopped, Linux UVC/ALSA compatibility |
| Wake detected but command ignored | Say command within four seconds; read monitor; use exact AutoPilot/Object Track/Stop grammar; reduce motor noise |
| One-breath command intermittent | Pause after Hey Arduino; wake and recognizer latency differ |
| App refuses to arm | NC contact must close D2 to GND when released; servo attach must succeed; correct UNO Q core and HardwareServo library |
| `waiting for fresh AI vision` | Model service not ready/too slow or old captured images. Check RAM/load; no other running examples; retain timeouts |
| `waiting for forward range` | Sonar timeout/no echo, incorrect divider/pins, narrow/angled surfaces, servo not centred/settled |
| Scan never succeeds | Camera and sonar must share mount; swapped scan angles; flat reflectors; side ranges >450 mm; fresh angle-matched AI result required |
| Stops close to obstacle and cannot turn | MCU pivot margin is 180 mm; no blind reversing. Stop, move car manually, select mode again |
| Moves backward/spins on a clear path | Raise chassis and verify each motor pair's polarity and driver direction constants |
| Target capture fails | Use a distinctive textured item, stable lighting and uncluttered centre; blank/shiny items may not form a usable template |
| Target returns but won't reacquire | It must resemble the frozen template and be within tested scale range; after major rotation say Object Track again |
| Stop works only in a quiet room | Relocate/isolate mic from motor/servo vibration and wind; lower speed; test noise. Use the physical power cut |
| MCU `command_timeout` | App heartbeat/RPC is late or disconnected; do not extend lease to mask it. Fix load/Bridge and select mode again |
| Q reboots under load | Verify separate servo/motor power, USB hub budget, cables and regulator voltage sag |
| CLI missing `Arduino_RPClite.h` | Use complete `sketch/sketch.yaml` profile, including transitive libraries, not only RouterBridge |
| Mac `bad CPU type` in `ctags` | Native compatible Arduino helper/toolchain or Linux firmware CI required; do not claim build success from behavior tests |

Start with motors disconnected. Check voltages before chasing software errors on an old 5 V shield. Do not troubleshoot live mechanical motion by raising the speed or loosening safety thresholds.
