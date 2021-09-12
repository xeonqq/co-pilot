from src.foreground_detector import ForegroundDetector
import cv2 as cv


class MotionDetector(object):
    @staticmethod
    def create_blob_detector():
        params = cv.SimpleBlobDetector_Params()
        params.filterByColor = 0
        params.filterByCircularity = 0
        params.filterByArea = 1
        params.minArea = 6
        params.maxArea = 240 * 180
        params.filterByConvexity = 1
        params.minConvexity = 0.5
        detector = cv.SimpleBlobDetector_create(params)
        return detector

    def __init__(self):
        self._foreground_detector = ForegroundDetector()
        self._blob_detector = MotionDetector.create_blob_detector()
        self._min_num_motion_key_points = 3
        self._min_key_point_size = 10
        self._target_image_shape = (180, 240)  # height x width

    def get_target_image_size(self):
        return self._target_image_shape

    def _has_key_point_size_larger_than(self, key_points):
        for keypoint in key_points:
            if keypoint.size > self._min_key_point_size:
                return True
        return False

    def detect_motion_keypoints(self, image_Y):
        assert image_Y.shape == self._target_image_shape
        foreground_mask = self._foreground_detector.apply(image_Y)
        keypoints = self._blob_detector.detect(foreground_mask)
        return keypoints

    def has_motion_in_image(self, image_Y):
        key_points = self.detect_motion_keypoints(image_Y)
        if (len(key_points) > self._min_num_motion_key_points) or self._has_key_point_size_larger_than(key_points):
            return True
        else:
            return False
