import unittest
import cv2 as cv
import numpy as np
from .context import src
from src.foreground_detector import ForegroundDetector


class ForegroundDectectionTest(unittest.TestCase):
    def test_foreground_detection(self):
        foreground_detector = ForegroundDetector()
        input_video = "tests/test_videos/recording_20210908-212416_049_car.mp4"
        capture = cv.VideoCapture(input_video)
        params = cv.SimpleBlobDetector_Params()
        params.filterByColor = 0
        params.filterByCircularity = 0
        params.filterByArea = 1
        params.minArea = 6
        params.maxArea = 240 * 180
        params.filterByConvexity = 1
        params.minConvexity = 0.5
        detector = cv.SimpleBlobDetector_create(params)
        if not capture.isOpened():
            print('Unable to open: ' + input_video)
            exit(0)
        while True:
            ret, frame = capture.read()
            if frame is None:
                break
            frame = cv.resize(frame, (240, 180))
            frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            fgMask = foreground_detector.apply(frame)
            keypoints = detector.detect(fgMask)

            # uncomment to see demo
            # im_with_keypoints = cv.drawKeypoints(frame, keypoints, np.array([]), (0,0,255), cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            # cv.imshow('FG Mask', fgMask)
            # cv.imshow("Keypoints", im_with_keypoints)

            # keyboard = cv.waitKey(30)
            # if keyboard == 'q' or keyboard == 27:
            #     break


if __name__ == '__main__':
    unittest.main()
