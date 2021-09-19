import io
import logging
import time
import threading
from PIL import Image
from math import ceil


class CameraCapturer(object):
    def __init__(self, camera, fps, pubsub, inference_config):
        self._pubsub = pubsub
        self._camera = camera
        self._dt = 1.0 / fps
        self._inference_resolution = inference_config.inference_resolution
        inference_width = int(ceil(self._inference_resolution[0] / 32) * 32)
        inference_scale = self._inference_resolution[0] / self._camera.resolution[0]
        inference_height = self._camera.resolution[1] * inference_scale
        inference_height = int(inference_height // 16 * 16)

        self._capture_resolution = (inference_width, inference_height)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stream = io.BytesIO()
        self._thread.start()
        # self._start = time.perf_counter()

    def _run(self):
        # capture time 60-80ms
        for _ in self._camera.capture_continuous(
            self._stream,
            format="rgb",
            resize=self._capture_resolution,
            use_video_port=True,
        ):
            # print("capture : {} ms".format((time.perf_counter() - self._start) * 1000))
            self._stream.truncate()
            self._stream.seek(0)
            img = Image.frombuffer(
                "RGB", self._capture_resolution, self._stream.getvalue()
            )

            current_time = time.perf_counter()
            logging.debug("capture at {}".format(current_time))
            self._pubsub.publish((img, current_time))
            logging.debug("exposure_speed:{}".format(self._camera.exposure_speed))
            # print("capture 2: {} ms".format((time.perf_counter() - start)*1000))
            time.sleep(self._dt)
            # self._start = time.perf_counter()
