import io
import logging
import time
import threading
from PIL import Image
from math import ceil


class CameraCapturer(object):
    def __init__(self, camera, fps, is_recording_query_func, pubsub, inference_config):
        self._pubsub = pubsub
        self._camera = camera
        self._dt = 1.0 / fps
        self._inference_resolution = inference_config.inference_resolution
        inference_width = int(ceil(self._inference_resolution[0] / 32) * 32)
        inference_scale = self._inference_resolution[0] / self._camera.resolution[0]
        inference_height = self._camera.resolution[1] * inference_scale
        inference_height = int(inference_height // 16 * 16)

        self._capture_resolution = (inference_width, inference_height)
        self._is_recording_query_func = is_recording_query_func
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stream = io.BytesIO()
        self._thread.start()

    def _run(self):
        while True:
            if self._is_recording_query_func():

                start = time.perf_counter()
                # 80-150ms
                self._camera.capture(
                    self._stream,
                    format="rgb",
                    resize=self._capture_resolution,
                    use_video_port=True,
                )
                self._stream.truncate()
                self._stream.seek(0)
                img = Image.frombuffer(
                    "RGB", self._capture_resolution, self._stream.getvalue()
                )

                current_time = time.perf_counter()
                logging.debug("capture at {}".format(current_time))
                # print("capture 1: {} ms".format((time.perf_counter() - start)*1000))
                self._pubsub.publish((img, current_time))
                logging.debug("exposure_speed:{}".format(self._camera.exposure_speed))
                # print("capture 2: {} ms".format((time.perf_counter() - start)*1000))
                time.sleep(self._dt)
