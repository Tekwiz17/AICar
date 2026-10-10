import queue
import threading
import time
import unittest
from collections import deque
from aicar.voice import Voice, TappedMicrophone
from aicar.control import Mode

class VoiceGateTests(unittest.TestCase):
    def setUp(self):
        self.events=[]
        self.voice=Voice.__new__(Voice)
        self.voice.request=self.events.append
        self.voice.window=4
        self.voice.until=0
        self.voice.recent=deque(maxlen=5)
        self.voice.lock=threading.Lock()

    def test_modes_require_official_wake_gate(self):
        self.voice.accept(Mode.AUTO)
        self.assertEqual(self.events,[])
        self.voice.wake()
        self.assertEqual(self.events,[Mode.STOP])
        self.voice.accept(Mode.TRACK)
        self.assertEqual(self.events,[Mode.STOP,Mode.TRACK])
        self.voice.accept(Mode.AUTO)
        self.assertEqual(self.events,[Mode.STOP,Mode.TRACK])

    def test_expired_wake_cannot_arm(self):
        self.voice.until=time.monotonic()-1
        self.voice.accept(Mode.AUTO)
        self.assertEqual(self.events,[])

    def test_one_breath_replay_only_with_recent_full_phrase(self):
        self.voice.recent.append((time.monotonic(),'hey arduino object track'))
        self.voice.wake()
        self.assertEqual(self.events,[Mode.STOP,Mode.TRACK])
        self.events.clear()
        self.voice.recent=deque([(time.monotonic()-3,'hey arduino auto pilot')])
        self.voice.wake()
        self.assertEqual(self.events,[Mode.STOP])

    def test_mic_has_only_one_capture_owner(self):
        class Source:
            def stream(self):
                yield [1,2,3]
                yield [4,5,6]
        chunks=[];faults=[]
        mic=TappedMicrophone(Source(),chunks.append,faults.append)
        self.assertEqual(list(mic.stream()),[[1,2,3],[4,5,6]])
        self.assertEqual(chunks,[[1,2,3],[4,5,6]])
        self.assertEqual(faults,[])
