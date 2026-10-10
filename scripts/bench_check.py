#!/usr/bin/env python3
"""Run INSIDE App Lab Python environment. Never arms or moves the chassis."""
import json
import time
from arduino.app_utils import Bridge

Bridge.call('stop_car',timeout=1)
for _ in range(15):
    status=json.loads(Bridge.call('car_status',timeout=1))
    assert not status['armed'], 'MCU unexpectedly armed'
    print(json.dumps(status),flush=True)
    time.sleep(.3)
print('Disarmed status check passed. Verify distance and physical switch changes manually.')
