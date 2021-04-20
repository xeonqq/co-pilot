import time
from datetime import datetime
import queue
import pathlib
import threading


class AsyncImageSaver(object):
    MAX_QUEUE_SIZE = 20

    def __init__(self, recording_folder):

        self._recording_folder = recording_folder
        self._recording_folder.mkdir(parents=True, exist_ok=True)
        self._rec_detection_folder = self._recording_folder.joinpath("detection")
        self._rec_detection_folder.mkdir(parents=True, exist_ok=True)

        self._task_queue = queue.Queue(AsyncImageSaver.MAX_QUEUE_SIZE)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop_and_join(self):
        self._task_queue.put(None)
        self._thread.join()

    def _run(self):
        for task in iter(self._task_queue.get, None):
            # current frame rate is ~1 fps
            time.sleep(0.1)
            task()

    def save_image_and_traffic_lights(self, image, traffic_lights):
        ti = datetime.now().strftime("%Y%m%d-%H%M%S.%f")[:-3]
        self._task_queue.put(lambda: self._save_image(image, ti))
        self._task_queue.put(lambda: self._save_traffic_lights(traffic_lights, ti))

    def _save_traffic_lights(self, traffic_lights, name_prefix):
        for i, t in enumerate(traffic_lights):
            filename = self._rec_detection_folder.joinpath(
                    "{0}_{1}_{2:4.2f}-{3}_{4:4.3f}.bmp".format(name_prefix, i, t.obj.score, t.cls, t.score)
            )
            t.image.save(filename)

    def _save_image(self, image, name_prefix):
        filename = self._rec_detection_folder.joinpath("{}_img.jpg".format(name_prefix))
        image.save(filename)
