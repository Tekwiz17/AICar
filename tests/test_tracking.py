import unittest
import numpy as np
import cv2
from aicar.tracking import AppearanceTracker, normalize_detections, blocked_by_ai

class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.pattern = np.random.default_rng(42).integers(0,256,(60,60,3),dtype=np.uint8)
        self.frame = np.zeros((240,320,3),dtype=np.uint8)
        self.frame[90:150,130:190] = self.pattern
        self.box = ('unknown',(130/320,90/240,190/320,150/240))
        self.tracker = AppearanceTracker()
        self.assertTrue(self.tracker.acquire(self.frame,[self.box]))

    def lock(self,frame,at=1):
        target=None
        for _ in range(3):target=self.tracker.update(frame,at)
        return target

    def test_unknown_object_moves_and_disappears(self):
        target=self.lock(self.frame)
        self.assertIsNotNone(target)
        moved=np.zeros_like(self.frame);moved[90:150,170:230]=self.pattern
        target=self.lock(moved,2)
        self.assertGreater(target.cx,.5)
        self.assertIsNone(self.tracker.update(np.zeros_like(self.frame),3))
        self.assertIsNotNone(self.lock(self.frame,4))

    def test_lookalikes_are_ambiguous(self):
        doubled=self.frame.copy();doubled[90:150,20:80]=self.pattern
        self.assertIsNone(self.lock(doubled))

    def test_textureless_capture_refused(self):
        self.assertFalse(AppearanceTracker().acquire(np.zeros_like(self.frame),[]))

    def test_bbox_scale_and_inference_failure(self):
        d=normalize_detections({'detection':[{'class_name':'person','bounding_box_xyxy':[32,64,160,256]}]},320,320)
        self.assertEqual(d[0][1],(.1,.2,.5,.8))
        self.assertEqual(normalize_detections({'detection':[]},320,320),[])
        with self.assertRaises(RuntimeError):normalize_detections(None,320,320)
        with self.assertRaises(ValueError):normalize_detections({'detection':[{'class_name':'x','bounding_box_xyxy':[0,0,400,500]}]},320,320)

    def test_ai_caution_and_target_exclusion(self):
        d=[('person',(.2,.1,.8,.95))]
        self.assertTrue(blocked_by_ai(d,.14))
        self.assertFalse(blocked_by_ai(d,.14,d[0][1]))
        d.append(('chair',(.4,.3,.95,1)))
        self.assertTrue(blocked_by_ai(d,.14,d[0][1]))
