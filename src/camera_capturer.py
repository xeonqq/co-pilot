import io
import logging
import time
import threading
from PIL import Image
from src.pubsub import Observable


class CameraCapturer(Observable):
    def __init__(self, camera, fps, is_recording_query_func, pubsub):
        Observable.__init__(self)
        self._pubsub = pubsub
        self._camera = camera
        self._dt = 1.0 / fps
        self._h_crop_keep_percentage = 0.6
        self._resolution = self._camera.resolution
        self._is_recording_query_func = is_recording_query_func
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stream = io.BytesIO()

    def start(self):
        self._thread.start()

    def get_id(self):
        return self.__class__.__name__

    def _crop_image(self, img):
        return img.crop(
            [
                0,
                0,
                self._resolution[0],
                int(self._resolution[1] * self._h_crop_keep_percentage),
            ]
        )

    def _run(self):
        while True:
            if self._is_recording_query_func():
                start = time.perf_counter()
                # 80-150ms
                self._camera.capture(
                    self._stream,
                    format="rgb",
                    use_video_port=True,
                )

                self._stream.truncate()
                self._stream.seek(0)
                img = Image.frombuffer("RGB", self._resolution, self._stream.getvalue())
                current_time = time.perf_counter()
                logging.debug("capture at {}".format(current_time))
                # print("capture 1: {} ms".format((time.perf_counter() - start)*1000))

                img = self._crop_image(img)
                self.publish((img, current_time))
                logging.debug("exposure_speed:{}".format(self._camera.exposure_speed))
                # print("capture 2: {} ms".format((time.perf_counter() - start)*1000))
                # print("dt {} s".format(self._dt))
                time.sleep(self._dt)
