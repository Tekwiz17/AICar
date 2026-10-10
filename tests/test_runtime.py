"""Exercise real runtime controller/Bridge integration using fake peripherals."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from aicar.control import Mode, Vision

class FakeBridge:
    def __init__(self):
        self.armed=False
        self.calls=[]
        self.fail_status=False
    def call(self,name,*args,**kwargs):
        self.calls.append((name,args))
        if name=='stop_car':self.armed=False;return True
        if name=='arm_car':self.armed=True;return True
        if name=='drive_car':return True
        if name=='car_status':
            if self.fail_status:raise TimeoutError('injected failure')
            return json.dumps({'distance_mm':1000,'sample_age_ms':20,'pan':90,
                               'settled_ms':1000,'estop':False,'armed':self.armed,'fault':'fake'})
        raise AssertionError(name)

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names=['arduino','arduino.app_utils','arduino.app_bricks',
               'arduino.app_bricks.object_detection','arduino.app_bricks.keyword_spotting',
               'arduino.app_peripherals','arduino.app_peripherals.camera',
               'arduino.app_peripherals.microphone']
        modules={name:types.ModuleType(name) for name in names}
        modules['arduino.app_utils'].App=object()
        modules['arduino.app_utils'].Bridge=FakeBridge()
        for mod,attr in [('object_detection','ObjectDetection'),('keyword_spotting','KeywordSpotting')]:
            setattr(modules['arduino.app_bricks.'+mod],attr,object)
        modules['arduino.app_peripherals.camera'].Camera=object
        modules['arduino.app_peripherals.microphone'].Microphone=object
        with patch.dict(sys.modules,modules):
            spec=importlib.util.spec_from_file_location('test_aicar_entry',Path(__file__).parents[1]/'python/main.py')
            cls.main=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.main)

    def setUp(self):
        self.bridge=FakeBridge()
        self.main.Bridge=self.bridge
        self.main.ObjectDetection=lambda **kwargs:types.SimpleNamespace(
            get_model_info=lambda:types.SimpleNamespace(image_input_width=320,image_input_height=320))
        self.main.Camera=lambda *args,**kwargs:None
        self.main.Microphone=lambda *args,**kwargs:None
        self.main.KeywordSpotting=lambda **kwargs:types.SimpleNamespace(
            model_info=types.SimpleNamespace(frequency=16000,axis_count=1),on_detect=lambda *args:None)
        self.main.Voice=lambda *args:types.SimpleNamespace(feed=lambda chunk:None,wake=lambda:None)
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime=self.main.Runtime({**self.main.CONFIG,'vosk_model_path':self.temp.name})
        self.runtime.started=True  # No real threads/devices; tick below is the production implementation.
        self.runtime.last_log=time.monotonic()
        self.runtime.vision=Vision(time.monotonic(),False)

    def tick(self):
        with patch.object(self.main.time,'sleep',lambda _:None):self.runtime.tick()

    def test_boot_auto_and_stop_sequence(self):
        self.tick()
        self.assertFalse(self.bridge.armed)
        self.runtime.request(Mode.AUTO)
        self.tick()
        self.assertTrue(self.bridge.armed)
        drive=[c for c in self.bridge.calls if c[0]=='drive_car'][-1]
        self.assertEqual(drive[1],(85,85,90))
        self.runtime.request(Mode.STOP)
        self.tick()
        self.assertFalse(self.bridge.armed)
        self.assertEqual(self.runtime.controller.mode,Mode.STOP)

    def test_worker_fault_overrides_drive_request(self):
        self.runtime.request(Mode.AUTO)
        self.runtime.fault('camera failed')
        self.tick()
        self.assertFalse(self.bridge.armed)
        self.assertEqual(self.runtime.controller.mode,Mode.STOP)
        self.assertEqual(self.runtime.controller.reason,'camera failed')

    def test_bridge_timeout_disarms_and_does_not_resume(self):
        self.runtime.request(Mode.AUTO);self.tick()
        self.bridge.fail_status=True;self.tick()
        self.assertFalse(self.bridge.armed)
        self.assertEqual(self.runtime.controller.mode,Mode.STOP)
        self.bridge.fail_status=False;self.tick()
        self.assertFalse(self.bridge.armed)
