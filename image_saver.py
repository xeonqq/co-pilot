import time
import queue
import pathlib
import threading


class AsyncImageSaver(object):
    MAX_QUEUE_SIZE = 50

    def __init__(self, folder):
        self._folder = folder
        pathlib.Path("{}".format(folder)).mkdir(parents=True, exist_ok=True)
        self._task_queue = queue.Queue(AsyncImageSaver.MAX_QUEUE_SIZE)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        for task in iter(self._task_queue.get, None):
            task()

    def save_object(self, image, obj):
        self._task_queue.put(lambda: self._crop_and_save_object(image, obj))

    def _crop_object(self, image, obj):
        obj_crop = image.crop([obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]])
        return obj_crop

    def _save_object(self, obj_crop, obj):
        filename = "{}/{}_{}.bmp".format(
            self._folder, obj.label, time.strftime("%Y%m%d-%H%M%S")
        )
        obj_crop.save(filename)

    def _crop_and_save_object(self, image, obj):
        self._save_object(self._crop_object(image, obj), obj)
