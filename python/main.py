"""Arduino App Lab entry point. No cloud calls or large language model."""
import json
from pathlib import Path
import queue
import threading
import time

from arduino.app_utils import App, Bridge
from arduino.app_bricks.object_detection import ObjectDetection
from arduino.app_bricks.keyword_spotting import KeywordSpotting
from arduino.app_peripherals.camera import Camera
from arduino.app_peripherals.microphone import Microphone
import cv2
from PIL import Image

from aicar.config import validate_config
from aicar.control import Controller, Mode, Telemetry, Vision
from aicar.tracking import AppearanceTracker, normalize_detections, blocked_by_ai
from aicar.voice import Voice, TappedMicrophone

ROOT = Path(__file__).resolve().parent
CONFIG = validate_config(json.loads((ROOT / "config.json").read_text()))


class Runtime:
    def __init__(self, config):
        self.c = config
        self.controller = Controller(config)
        self.lock = threading.RLock()
        self.requests = queue.Queue(maxsize=16)
        self.faults = queue.Queue(maxsize=16)
        self.vision = Vision()
        self.telemetry = Telemetry()
        self.running = threading.Event()
        self.running.set()
        self.started = False
        self.last_log = 0
        self.model = ObjectDetection(confidence=.55)
        info = self.model.get_model_info()
        self.model_size = (info.image_input_width, info.image_input_height)
        if min(self.model_size) <= 0:
            raise RuntimeError("object model has no image dimensions")
        self.camera = Camera(config["camera_source"],
                             resolution=(config["camera_width"],config["camera_height"]),
                             fps=config["camera_fps"])
        model_path = Path(config["vosk_model_path"])
        if not model_path.is_absolute():
            model_path = ROOT / model_path
        if not model_path.is_dir():
            raise RuntimeError(f"Download the Vosk model first: {model_path}; see docs/SETUP.md")
        self.voice = Voice(str(model_path), self.request, self.fault, config["voice_window_s"])
        mic_source = config["microphone_source"]
        mic = Microphone(mic_source, sample_rate=16000, channels=1)
        self.keyword = KeywordSpotting(mic=TappedMicrophone(mic,self.voice.feed,self.fault))
        if int(self.keyword.model_info.frequency) != 16000 or self.keyword.model_info.axis_count != 1:
            raise RuntimeError("This voice adapter requires a 16 kHz mono Hey Arduino model")
        def on_wake():
            self.voice.wake()
        self.keyword.on_detect("hey_arduino", on_wake)
        self.vision_thread = threading.Thread(target=self.camera_loop, name="vision", daemon=True)

    def request(self, mode):
        try:
            self.requests.put_nowait(mode)
        except queue.Full:
            self.fault("mode command queue overflow")

    def fault(self, message):
        try:
            self.faults.put_nowait(message)
        except queue.Full:
            pass

    def camera_loop(self):
        tracker = AppearanceTracker(self.c["tracker_threshold"], self.c["tracker_ambiguity_margin"])
        revision = -1
        capture_at = 0
        next_inference = 0
        ai_at = -1e9
        ai_pan = 90
        detections = []
        try:
            self.camera.start()
            while self.running.is_set():
                with self.lock:
                    mode, rev = self.controller.mode, self.controller.revision
                    telemetry = self.telemetry
                if revision != rev:
                    revision = rev
                    tracker.reset()
                    capture_at = time.monotonic() + self.c["target_capture_seconds"]
                captured_at = time.monotonic()
                frame = self.camera.capture()
                if frame is None:
                    time.sleep(.02)
                    continue
                frame = cv2.resize(frame,(self.c["camera_width"],self.c["camera_height"]))
                if captured_at >= next_inference and telemetry.settled_ms >= self.c["scan_settle_ms"]:
                    # Submit EXACT model dimensions, so bbox coordinates have a known scale.
                    image = Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize(self.model_size)
                    result = self.model.detect(image)
                    detections = normalize_detections(result,*self.model_size)
                    ai_at, ai_pan = captured_at, telemetry.pan
                    next_inference = time.monotonic()+self.c["inference_interval_s"]
                target = None
                if mode == Mode.TRACK and abs(telemetry.pan-self.c["servo_center"]) <= 3 and telemetry.settled_ms >= self.c["scan_settle_ms"]:
                    if tracker.template is None and captured_at >= capture_at:
                        if not tracker.acquire(frame,detections) and captured_at > capture_at+5:
                            self.fault("target has insufficient visible texture; select Object Track again")
                    target = tracker.update(frame,captured_at,self.c["target_lock_frames"])
                blocked = blocked_by_ai(detections,self.c["visual_obstacle_area"],
                                        target.box if target else None)
                with self.lock:
                    # Discard work from a mode that changed while inference was in progress.
                    if rev == self.controller.revision:
                        self.vision = Vision(ai_at,blocked,target,ai_pan)
        except Exception as e:
            self.fault(f"vision failed: {e}")
        finally:
            self.camera.stop()

    def tick(self):
        if not self.started:
            Bridge.call("stop_car",timeout=.25)
            self.voice.thread.start()
            self.vision_thread.start()
            self.started = True
        try:
            # Process requests on this one thread: no concurrent motor RPC calls.
            requested = None
            while not self.requests.empty():
                requested = self.requests.get_nowait()
            fault = None
            while not self.faults.empty():
                fault = self.faults.get_nowait()
            if fault:
                requested = Mode.STOP
                with self.lock:
                    self.controller.stop(fault)
                print(f"FAULT: {fault}",flush=True)
            if requested is not None:
                Bridge.call("stop_car",timeout=.25)
                with self.lock:
                    self.controller.set_mode(Mode.STOP,time.monotonic())
                    if fault:
                        self.controller.reason = fault
                if requested != Mode.STOP:
                    if not Bridge.call("arm_car",timeout=.25):
                        raise RuntimeError("MCU refused to arm; check physical stop and servo")
                    with self.lock:
                        self.controller.set_mode(requested,time.monotonic())
                    if requested == Mode.TRACK:
                        print("Object Track: place the item at camera centre; capture in 3 seconds",flush=True)
            status = json.loads(Bridge.call("car_status",timeout=.25))
            with self.lock:
                self.telemetry = Telemetry.from_dict(status)
                output = self.controller.step(time.monotonic(),self.telemetry,self.vision)
                mode = self.controller.mode
            if mode == Mode.STOP:
                Bridge.call("stop_car",timeout=.25)
            if not Bridge.call("drive_car",output.left,output.right,output.pan,timeout=.25):
                raise RuntimeError("MCU rejected drive command")
            if time.monotonic()-self.last_log >= 1:
                print(json.dumps({"mode":mode.value,"reason":output.reason,
                                  "pwm":[output.left,output.right],"status":status}),flush=True)
                self.last_log = time.monotonic()
        except Exception as e:
            with self.lock:
                self.controller.stop(f"bridge/control failure: {e}")
            print(f"Control stopped: {e}",flush=True)
            try:
                Bridge.call("stop_car",timeout=.25)
            except Exception:
                pass  # MCU lease independently expires within 500 ms + one bounded ping.
        time.sleep(.08)

    def stop(self):
        self.running.clear()
        self.voice.stop()
        try:
            Bridge.call("stop_car",timeout=.25)
        except Exception:
            pass


def main():
    runtime = None
    try:
        # Initialization failures leave the MCU's boot state disarmed.
        Bridge.call("stop_car",timeout=.25)
        runtime = Runtime(CONFIG)
        App.run(user_loop=runtime.tick)
    finally:
        if runtime:
            runtime.stop()


if __name__ == "__main__":
    main()
