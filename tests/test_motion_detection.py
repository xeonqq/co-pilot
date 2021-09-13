import unittest
import cv2 as cv
import numpy as np
from .context import src
from collections import namedtuple
from src.motion_detector import MotionDetector


def count_motion_frames(motion_detection_results):
    return sum(x is True for x in motion_detection_results)


MotionDetectorConfig = namedtuple(
    "MotionDetectorConfig", ["width", "height"]
)

class MotionDetectorTest(unittest.TestCase):
    def test_detect_motion_from_video(self):
        config = MotionDetectorConfig(240, 180)
        motion_detector = MotionDetector(config)

        input_video = "tests/test_videos/recording_20210908-212416_049_car.mp4"
        capture = cv.VideoCapture(input_video)
        motion_detection_results = []
        if not capture.isOpened():
            print('Unable to open: ' + input_video)
            exit(0)
        while True:
            ret, frame = capture.read()
            if frame is None:
                break
            frame = cv.resize(frame, (240, 180))
            frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            has_motion = motion_detector.has_motion_in_image(frame)
            motion_detection_results.append(has_motion)

            num_motion_frames = count_motion_frames(motion_detection_results)
        self.assertGreater(len(motion_detection_results) - num_motion_frames, num_motion_frames)
        self.assertGreater(num_motion_frames, 10)
        self.assertTrue(motion_detection_results[-5])
        self.assertFalse(motion_detection_results[5])


if __name__ == '__main__':
    unittest.main()
