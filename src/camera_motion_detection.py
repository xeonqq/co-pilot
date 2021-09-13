import io
import logging
import time
import threading
import numpy as np

from src.motion_detector import MotionDetector


class CameraMotionDetection(object):
    def __init__(self, camera, fps, motion_detection_config):
        self._camera = camera
        self._dt = 1.0 / fps

        self._capture_resolution = (motion_detection_config.width, motion_detection_config.height)
        self._num_pixels = self._capture_resolution[0] * self._capture_resolution[1]
        self._observers = []

        self._motion_detector = MotionDetector(motion_detection_config)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stream = io.BytesIO()
        self._thread.start()

    def add_observer(self, observer):
        self._observers.append(observer)

    def _notify(self):
        for obs in self._observers:
            obs.notify(self)

    def _run(self):
        while True:
            start = time.perf_counter()
            self._camera.capture(
                self._stream,
                format="yuv",
                resize=self._capture_resolution,
                use_video_port=True,
            )
            self._stream.truncate()
            self._stream.seek(0)
            Y = np.fromfile(self._stream, dtype=np.uint8, count=self._num_pixels). \
                reshape((self._capture_resolution[1], self._capture_resolution[0]))
            if self._motion_detector.has_motion_in_image(Y):
                self._notify()
            logging.debug("capture+motion: {} ms".format((time.perf_counter() - start) * 1000))
            time.sleep(self._dt)
