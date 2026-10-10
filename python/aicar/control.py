"""Deterministic local navigation. All times are monotonic seconds."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections import deque
import random


class Mode(str, Enum):
    STOP = "Stop"
    AUTO = "AutoPilot"
    TRACK = "ObjectTrack"


@dataclass(frozen=True)
class Target:
    cx: float
    area_ratio: float  # Current area / area at initial capture.
    timestamp: float
    confidence: float
    box: tuple | None = None


@dataclass(frozen=True)
class Vision:
    timestamp: float = -1e9
    blocked: bool = True
    target: Target | None = None
    pan: int = 90


@dataclass(frozen=True)
class Telemetry:
    distance_mm: int = -1
    sample_age_ms: int = 999999
    pan: int = 90
    settled_ms: int = 0
    estop: bool = True
    armed: bool = False
    fault: str = "boot"

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})


@dataclass(frozen=True)
class Output:
    left: int = 0
    right: int = 0
    pan: int = 90
    reason: str = "stopped"


class Controller:
    def __init__(self, config, rng=None):
        self.c = config
        self.rng = rng or random.Random()
        self.mode = Mode.STOP
        self.revision = 0
        self.phase = "cruise"
        self.scans = {}
        self.scan_index = 0
        self.turns = deque()
        self.last_direction = 0
        self.last_cruise = 0.0
        self.deadline = 0.0
        self.reason = "startup; say Hey Arduino followed by a mode"

    def set_mode(self, mode, now):
        self.mode = Mode(mode)
        self.revision += 1
        self.phase = "cruise"
        self.scans.clear()
        self.turns.clear()
        self.last_cruise = now
        self.reason = "mode selected"

    def stop(self, reason):
        if self.mode != Mode.STOP:
            self.revision += 1
        self.mode = Mode.STOP
        self.reason = reason

    def step(self, now, telemetry, vision):
        c = self.c
        center = c["servo_center"]
        def out(left=0, right=0, pan=center, reason="stopped"):
            return Output(left, right, pan, reason)

        if telemetry.estop:
            self.stop("physical stop pressed or disconnected")
        if self.mode == Mode.STOP:
            return out(reason=self.reason)
        if not telemetry.armed:
            self.stop("MCU disarmed; select a mode again")
            return out(reason=self.reason)
        if now - vision.timestamp > c["vision_timeout_s"]:
            if self.phase == "scan":
                if now >= self.deadline:
                    self.stop("scan vision unavailable")
                    return out(reason=self.reason)
                angle = [c["servo_left"], c["servo_right"]][self.scan_index]
                return out(pan=angle, reason="stationary scan: waiting for fresh AI vision")
            return out(reason="waiting for fresh AI vision")
        range_ok = (telemetry.distance_mm > 0 and
                    telemetry.sample_age_ms <= c["range_timeout_ms"] and
                    telemetry.settled_ms >= c["scan_settle_ms"])
        centered = abs(telemetry.pan - center) <= 3

        if self.mode == Mode.TRACK:
            if abs(vision.pan - center) > 3:
                return out(reason="waiting for centered camera vision")
            target = vision.target
            if not target or now - target.timestamp > c["target_timeout_s"]:
                return out(reason="target lost: waiting in place")
            if not range_ok or not centered:
                return out(reason="waiting for forward range")
            if telemetry.distance_mm <= c["obstacle_mm"] or vision.blocked:
                return out(reason="obstacle: waiting for a clear path")
            error = target.cx - 0.5
            if abs(error) > c["target_center_tolerance"]:
                # Differential pivot; the MCU independently enforces close-range protection.
                p = c["turn_pwm"]
                return out(p if error > 0 else -p, -p if error > 0 else p,
                           reason="centering locked target")
            if target.area_ratio >= c["target_size_hold_ratio"]:
                return out(reason="target at desired distance")
            return out(c["follow_pwm"], c["follow_pwm"], reason="following locked target")

        while self.turns and now - self.turns[0] > 20:
            self.turns.popleft()
        if len(self.turns) >= c["max_turns_per_20s"]:
            self.stop("repeated turns: stuck; move car and select AutoPilot again")
            return out(reason=self.reason)

        if self.phase == "scan":
            angles = [c["servo_left"], c["servo_right"]]
            angle = angles[self.scan_index]
            if (abs(telemetry.pan - angle) <= 2 and range_ok and
                    abs(vision.pan - angle) <= 2):
                self.scans[angle] = min(telemetry.distance_mm, c["obstacle_mm"]) if vision.blocked else telemetry.distance_mm
                self.scan_index += 1
                if self.scan_index == len(angles):
                    left = self.scans[angles[0]]
                    right = self.scans[angles[1]]
                    if max(left, right) < c["turn_clearance_mm"]:
                        self.stop("no clear exit: waiting for a new mode command")
                        return out(reason=self.reason)
                    # Penalise repeating the same turn; break ties without circling forever.
                    scores = [left - (120 if self.last_direction == -1 else 0),
                              right - (120 if self.last_direction == 1 else 0)]
                    self.last_direction = -1 if scores[0] > scores[1] else 1
                    if self.scans[angles[0 if self.last_direction == -1 else 1]] < c["turn_clearance_mm"]:
                        self.last_direction *= -1
                    self.phase = "recenter"
                    return out(reason="recentering before bounded turn")
                angle = angles[self.scan_index]
            elif now >= self.deadline:
                self.stop("scan range unavailable")
                return out(reason=self.reason)
            return out(pan=angle, reason="stationary clearance scan")

        if self.phase == "recenter":
            if centered and range_ok and abs(vision.pan - center) <= 3:
                self.phase = "turn"
                self.deadline = now + c["turn_duration_s"]
                self.turns.append(now)
            return out(reason="recentering sensors")

        if self.phase == "turn":
            if now >= self.deadline:
                self.phase = "cruise"
                self.last_cruise = now
                return out(reason="turn complete; checking path")
            if not range_ok or not centered or telemetry.distance_mm <= 180:
                return out(reason="turn blocked by range")
            p = c["turn_pwm"] * self.last_direction
            return out(p, -p, reason="bounded turn")

        if not range_ok or not centered or abs(vision.pan - center) > 3:
            return out(reason="waiting for forward range and vision")
        if telemetry.distance_mm <= c["obstacle_mm"] or vision.blocked:
            self.phase = "scan"
            self.scan_index = 0
            self.scans.clear()
            self.deadline = now + 5
            return out(pan=c["servo_left"], reason="obstacle: stop and scan")
        if now - self.last_cruise > c["roam_straight_s"]:
            self.last_direction = self.rng.choice([-1, 1])
            self.phase = "turn"
            self.deadline = now + min(0.25, c["turn_duration_s"])
            self.turns.append(now)
            return out(reason="small heading change")
        return out(c["cruise_pwm"], c["cruise_pwm"], reason="exploring forward")
