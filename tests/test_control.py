import json
from pathlib import Path
import random
import unittest
from dataclasses import replace
from aicar.control import Controller, Mode, Telemetry, Target, Vision
from aicar.commands import parse_command
from aicar.config import validate_config

CONFIG = json.loads((Path(__file__).parents[1]/'python/config.json').read_text())

class ControlTests(unittest.TestCase):
    def setUp(self):
        self.ctrl = Controller(CONFIG,random.Random(1))
        self.t = Telemetry(1000,30,90,1000,False,True,'running')
        self.v = Vision(10,False)

    def test_starts_stopped_and_never_autoresumes(self):
        self.assertEqual(self.ctrl.step(10,self.t,self.v).left,0)
        self.ctrl.set_mode(Mode.AUTO,10)
        self.assertGreater(self.ctrl.step(10,self.t,self.v).left,0)
        self.ctrl.stop('voice stop')
        for i in range(10):
            self.assertEqual(self.ctrl.step(10+i,self.t,Vision(10+i,False)).left,0)

    def test_stale_vision_missing_range_and_wrong_pan_hold(self):
        self.ctrl.set_mode(Mode.AUTO,10)
        self.assertEqual(self.ctrl.step(12,self.t,self.v).left,0)
        for t in [replace(self.t,distance_mm=-1),replace(self.t,sample_age_ms=251),
                  replace(self.t,pan=125),replace(self.t,settled_ms=100)]:
            self.assertEqual(self.ctrl.step(10,t,self.v).left,0)

    def test_estop_and_disarm_latch_stop(self):
        for t in [replace(self.t,estop=True),replace(self.t,armed=False)]:
            self.ctrl.set_mode(Mode.AUTO,10)
            self.ctrl.step(10,t,self.v)
            self.assertEqual(self.ctrl.mode,Mode.STOP)
            self.assertEqual(self.ctrl.step(10,self.t,self.v).left,0)

    def test_lost_target_waits_without_searching(self):
        self.ctrl.set_mode(Mode.TRACK,10)
        self.assertEqual(self.ctrl.step(10,self.t,self.v).left,0)
        target = Target(.5,.6,10,.95)
        self.assertGreater(self.ctrl.step(10,self.t,Vision(10,False,target)).left,0)
        out = self.ctrl.step(10.6,self.t,Vision(10.6,False,target))
        self.assertEqual((out.left,out.right,out.pan),(0,0,90))
        self.assertGreater(self.ctrl.step(11,self.t,Vision(11,False,replace(target,timestamp=11))).left,0)

    def test_follow_stops_for_obstacle_and_size(self):
        self.ctrl.set_mode(Mode.TRACK,10)
        for v in [Vision(10,True,Target(.5,.5,10,.9)),Vision(10,False,Target(.5,1.1,10,.9))]:
            self.assertEqual(self.ctrl.step(10,self.t,v).left,0)
        self.assertEqual(self.ctrl.step(10,replace(self.t,distance_mm=320),Vision(10,False,Target(.5,.5,10,.9))).left,0)

    def test_obstacle_scan_then_bounded_turn(self):
        self.ctrl.set_mode(Mode.AUTO,10)
        output = self.ctrl.step(10,replace(self.t,distance_mm=330),self.v)
        self.assertEqual((output.left,output.right,output.pan),(0,0,125))
        # A result from a different camera angle cannot complete a scan.
        self.ctrl.step(10.5,replace(self.t,pan=125),Vision(10.5,False,pan=90))
        self.assertEqual(self.ctrl.scan_index,0)
        self.ctrl.step(11,replace(self.t,pan=125,distance_mm=1000),Vision(11,False,pan=125))
        self.ctrl.step(12,replace(self.t,pan=55,distance_mm=600),Vision(12,False,pan=55))
        self.assertEqual(self.ctrl.phase,'recenter')
        self.ctrl.step(13,self.t,Vision(13,False))
        out=self.ctrl.step(13.1,self.t,Vision(13.1,False))
        self.assertLess(out.left,0);self.assertGreater(out.right,0)
        out=self.ctrl.step(14,self.t,Vision(14,False))
        self.assertEqual((out.left,out.right),(0,0))
        self.assertEqual(self.ctrl.phase,'cruise')

    def test_missing_echo_and_repeated_turns_stop(self):
        self.ctrl.set_mode(Mode.AUTO,10)
        self.ctrl.step(10,replace(self.t,distance_mm=330),self.v)
        self.ctrl.step(16,replace(self.t,pan=125,distance_mm=-1),Vision(16,False,pan=125))
        self.assertEqual(self.ctrl.mode,Mode.STOP)
        self.ctrl.set_mode(Mode.AUTO,20)
        self.ctrl.turns.extend([20]*CONFIG['max_turns_per_20s'])
        self.ctrl.step(21,self.t,Vision(21,False))
        self.assertEqual(self.ctrl.mode,Mode.STOP)

    def test_exact_commands_and_config(self):
        self.assertEqual(parse_command('Hey Arduino, Stop'.replace(',','')),Mode.STOP)
        self.assertEqual(parse_command('object track'),Mode.TRACK)
        self.assertEqual(parse_command('auto pilot'),Mode.AUTO)
        self.assertIsNone(parse_command('do not stop'))
        validate_config(CONFIG)
        with self.assertRaises(ValueError):validate_config({**CONFIG,'cruise_pwm':255})

    def test_stale_scan_keeps_sensors_stationary_and_times_out(self):
        self.ctrl.set_mode(Mode.AUTO,10)
        self.ctrl.step(10,replace(self.t,distance_mm=330),self.v)
        out=self.ctrl.step(12,replace(self.t,pan=125),self.v)
        self.assertEqual((out.left,out.right,out.pan),(0,0,125))
        self.ctrl.step(16,replace(self.t,pan=125),self.v)
        self.assertEqual(self.ctrl.mode,Mode.STOP)
