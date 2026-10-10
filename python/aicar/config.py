"""Reject settings outside the MCU's independent operating envelope."""
def validate_config(c):
    if c['servo_center'] != 90 or not all(55 <= c[k] <= 125 for k in ['servo_left','servo_right']):
        raise ValueError('servo centre must be 90 and scans within 55..125; also calibrate physical horn')
    if c['servo_left'] == c['servo_right']:
        raise ValueError('scan angles must differ')
    if not all(0 < c[k] <= 110 for k in ['cruise_pwm','follow_pwm','turn_pwm']):
        raise ValueError('motor PWM must be within 1..110')
    if c['obstacle_mm'] < 350 or c['turn_clearance_mm'] < c['obstacle_mm']:
        raise ValueError('obstacle and turn clearances are too small')
    if not 0 < c['range_timeout_ms'] <= 250 or c['scan_settle_ms'] < 400:
        raise ValueError('range freshness/servo settle settings violate MCU envelope')
    if not 0 < c['vision_timeout_s'] <= 2 or not 0 < c['target_timeout_s'] <= .5:
        raise ValueError('vision/target timeouts must remain bounded')
    if not 0 < c['turn_duration_s'] <= .8 or not 2 <= c['max_turns_per_20s'] <= 6:
        raise ValueError('turn duration/count must remain bounded')
    if not .7 <= c['tracker_threshold'] <= 1 or not 2 <= c['target_lock_frames'] <= 10:
        raise ValueError('tracker confidence/confirmation settings invalid')
    return c
