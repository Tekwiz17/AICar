"""Small, model-independent appearance lock for objects outside YOLO's classes.

A frozen template avoids silently drifting onto another object. Low confidence or
ambiguous lookalikes produce no target. This is not biometric identification.
"""
import cv2
import numpy as np
from .control import Target


class AppearanceTracker:
    def __init__(self, threshold=0.80, ambiguity_margin=0.035):
        self.threshold = threshold
        self.margin = ambiguity_margin
        self.template = None
        self.confirmations = 0
        self.last_center = None

    def reset(self):
        self.template = None
        self.confirmations = 0
        self.last_center = None

    def acquire(self, frame, detections):
        h, w = frame.shape[:2]
        # Prefer an AI-detected box containing the reticle. Otherwise capture
        # a 30% central region, allowing previously unknown objects.
        candidates = [d for d in detections if
                      d[1][0] <= .5 <= d[1][2] and d[1][1] <= .5 <= d[1][3] and
                      (d[1][2] - d[1][0]) * (d[1][3] - d[1][1]) < .7]
        if candidates:
            _, box = min(candidates, key=lambda d:
                         abs((d[1][0]+d[1][2])/2-.5)+abs((d[1][1]+d[1][3])/2-.5))
        else:
            box = (.35, .35, .65, .65)
        x1, y1, x2, y2 = [round(box[0]*w), round(box[1]*h), round(box[2]*w), round(box[3]*h)]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        template = gray[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
        if template.size == 0 or min(template.shape) < 12 or float(template.std()) < 10:
            return False
        self.template = template.copy()
        self.confirmations = 0
        self.last_center = None
        return True

    def update(self, frame, timestamp, required_frames=3):
        if self.template is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        candidates = []
        maps = []
        th, tw = self.template.shape
        for scale in (.65, .8, 1.0, 1.2, 1.45):
            sw, sh = round(tw*scale), round(th*scale)
            if min(sw,sh) < 10 or sw >= w or sh >= h:
                continue
            template = cv2.resize(self.template, (sw,sh))
            scores = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, (x,y) = cv2.minMaxLoc(scores)
            candidates.append((score,x,y,sw,sh))
            maps.append((scores,sw,sh))
        if not candidates:
            return None
        score,x,y,sw,sh = max(candidates)
        cx,cy = x+sw/2,y+sh/2
        second = -1.0
        for scores,mw,mh in maps:
            other = scores.copy()
            # Ignore peaks describing the same object at another scale/offset.
            ox,oy = cx-mw/2,cy-mh/2
            x1,x2 = max(0,int(ox-sw*.65)), min(other.shape[1],int(ox+sw*.65)+1)
            y1,y2 = max(0,int(oy-sh*.65)), min(other.shape[0],int(oy+sh*.65)+1)
            other[y1:y2,x1:x2] = -1
            second = max(second,float(other.max()))
        if score < self.threshold or score-second < self.margin:
            self.confirmations = 0
            self.last_center = None
            return None
        center = (cx/w,cy/h)
        if self.last_center and abs(center[0]-self.last_center[0])+abs(center[1]-self.last_center[1]) > .25:
            self.confirmations = 0
        self.last_center = center
        self.confirmations += 1
        if self.confirmations < required_frames:
            return None
        return Target(cx/w, sw*sh/(tw*th), timestamp, float(score), (x/w,y/h,(x+sw)/w,(y+sh)/h))


def normalize_detections(result, model_width, model_height):
    """The Brick uses model-input pixels and percentage confidence strings."""
    if result is None:
        raise RuntimeError("AI inference failed; an empty successful result must be a dict")
    detections = []
    for d in result.get("detection", []):
        box = d["bounding_box_xyxy"]
        if len(box) != 4 or not all(np.isfinite(v) for v in box):
            raise ValueError("invalid model bounding box")
        normalized = (box[0]/model_width,box[1]/model_height,
                      box[2]/model_width,box[3]/model_height)
        if not (0 <= normalized[0] < normalized[2] <= 1.01 and
                0 <= normalized[1] < normalized[3] <= 1.01):
            raise ValueError("model bounding boxes do not match model input dimensions")
        detections.append((d["class_name"], normalized))
    return detections


def blocked_by_ai(detections, area_threshold, target_box=None):
    for _, (x1,y1,x2,y2) in detections:
        if target_box:
            a,b,c,d = target_box
            intersection = max(0,min(c,x2)-max(a,x1))*max(0,min(d,y2)-max(b,y1))
            union = (c-a)*(d-b)+(x2-x1)*(y2-y1)-intersection
            if union > 0 and intersection/union > .55:
                continue  # Locked target distance is still protected by sonar.
        # Coarse visual caution zone; never interpreted as metric distance.
        if x1 < .65 and x2 > .35 and y2 > .65 and (x2-x1)*(y2-y1) >= area_threshold:
            return True
    return False
