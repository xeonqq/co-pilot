import cv2 as cv


class ForegroundDetector(object):
    def __init__(self):
        self._background_sub = cv.createBackgroundSubtractorMOG2()

    def apply(self, image_Y):
        foreground_mask = self._background_sub.apply(image_Y)
        return foreground_mask
