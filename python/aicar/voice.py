"""One USB microphone feeds both the official wake Brick and Vosk.

No second ALSA owner, no cloud speech service, bounded audio queue.
"""
import json
import queue
import threading
import time
from collections import deque
import numpy as np
from .commands import parse_command
from .control import Mode


class TappedMicrophone:
    """Duck-typed BaseMicrophone adapter accepted by KeywordSpotting."""
    def __init__(self, source, sink, fault):
        self.source, self.sink, self.fault = source, sink, fault

    def __getattr__(self, name):
        return getattr(self.source, name)

    def stream(self):
        try:
            for chunk in self.source.stream():
                self.sink(chunk)
                yield chunk  # Unchanged int16 samples for the wake model.
        except Exception:
            self.fault("microphone stream failed")
            raise


class Voice:
    def __init__(self, model_path, request, fault, window=4):
        from vosk import Model, KaldiRecognizer
        self.recognizer = KaldiRecognizer(Model(model_path), 16000, json.dumps([
            "hey arduino auto pilot", "hey arduino object track", "hey arduino stop",
            "auto pilot", "object track", "stop", "[unk]"
        ]))
        self.request, self.fault, self.window = request, fault, window
        self.audio = queue.Queue(maxsize=30)
        self.until = 0.0
        self.recent = deque(maxlen=5)
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()
        self.last_audio = time.monotonic()
        self.thread = threading.Thread(target=self.run, name="voice", daemon=True)

    def feed(self, chunk):
        self.last_audio = time.monotonic()
        try:
            self.audio.put_nowait(np.asarray(chunk, dtype='<i2').tobytes())
        except queue.Full:
            self.fault("voice processing fell behind")
            # Do not execute a delayed driving command from queued audio.
            with self.lock:
                self.until = 0
            while True:
                try:
                    self.audio.get_nowait()
                except queue.Empty:
                    break

    def wake(self):
        now = time.monotonic()
        pending = None
        with self.lock:
            self.until = now + self.window
            for at,text in reversed(self.recent):
                if now-at < 1.5 and text.startswith("hey arduino "):
                    pending = parse_command(text)
                    break
        self.request(Mode.STOP)  # Freeze while listening for the new command.
        print("Hey Arduino detected: listening for AutoPilot, Object Track or Stop", flush=True)
        if pending is not None:
            self.accept(pending)

    def accept(self, mode):
        with self.lock:
            if time.monotonic() > self.until:
                return
            self.until = 0
        self.request(mode)

    def run(self):
        try:
            while self.running.is_set():
                try:
                    pcm = self.audio.get(timeout=.2)
                except queue.Empty:
                    if time.monotonic()-self.last_audio > 2:
                        self.fault("microphone audio stale")
                    continue
                if self.recognizer.AcceptWaveform(pcm):
                    text = json.loads(self.recognizer.Result()).get("text", "")
                    with self.lock:
                        self.recent.append((time.monotonic(),text))
                    mode = parse_command(text)
                    if mode is not None:
                        self.accept(mode)
                else:
                    text = json.loads(self.recognizer.PartialResult()).get("partial", "")
                    if parse_command(text) == Mode.STOP:
                        self.accept(Mode.STOP)
        except Exception as e:
            self.fault(f"voice recognizer failed: {e}")

    def stop(self):
        self.running.clear()
