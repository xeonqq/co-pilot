import io
import time
import threading
from PIL import Image


class CameraCapturer(object):
    def __init__(self, camera, fps, is_recording_query_func, subscriber_queue):
        self._queue = subscriber_queue
        self._camera = camera
        self._dt = 1.0 / fps
        self._resolution = self._camera.resolution
        self._is_recording_query_func = is_recording_query_func
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            if self._is_recording_query_func():
                stream = io.BytesIO()

                # start = time.perf_counter()
                # 80-150ms
                self._camera.capture(
                    stream,
                    format="rgb",
                    use_video_port=True,
                )
                # print("capture: {} ms".format((time.perf_counter() - start)*1000))
                stream.truncate()
                stream.seek(0)
                img = Image.frombuffer("RGB", self._resolution, stream.getvalue())
                self._queue.put(img)
                time.sleep(self._dt)
