import time
import queue
import pathlib
import threading


class AsyncImageSaver(object):
    MAX_QUEUE_SIZE = 50

    def __init__(self, folder, recording_folder):
        self._folder = folder
        self._recording_foler = recording_folder

        self._recording_folder = pathlib.Path(recording_folder).joinpath(
            time.strftime("%Y%m%d-%H%M%S")
        )
        self._recording_folder.mkdir(parents=True, exist_ok=True)

        pathlib.Path("{}".format(folder)).mkdir(parents=True, exist_ok=True)
        self._task_queue = queue.Queue(AsyncImageSaver.MAX_QUEUE_SIZE)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def join(self):
        self._task_queue.put(None)
        self._thread.join()

    def _run(self):
        for task in iter(self._task_queue.get, None):
            task()

    def save(self, image):
        self._task_queue.put(lambda: self._save_image(image))

    def _save_image(self, image):
        filename = self._recording_folder.joinpath(
            "{}.jpg".format(time.strftime("%Y%m%d-%H%M%S"))
        )
        image.save(filename)

    def save_object(self, image, obj, name):
        obj_crop = self._crop_object(image, obj)
        self._task_queue.put(lambda: self._save_object(obj_crop, obj, name))

    def _crop_object(self, image, obj):
        obj_crop = image.crop([obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]])
        return obj_crop

    def _save_object(self, obj_crop, obj, name):
        if name == "":
            name = time.strftime("%Y%m%d-%H%M%S")
        filename = "{}/{}_{}.bmp".format(self._folder, obj.label, name)
        obj_crop.save(filename)

    def _crop_and_save_object(self, image, obj, name):
        self._save_object(self._crop_object(image, obj), obj, name)
