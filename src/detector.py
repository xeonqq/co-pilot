import logging
import threading
import time

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file

from .utils import (
    crop_objects,
    tiles_location_gen,
    reposition_bounding_box,
    TileConfig,
    union_of_intersected_objects,
    Object,
)
from src.pubsub import Observable, Observer


class Detector(Observable, Observer):
    def __init__(self, interpreter, args):
        Observable.__init__(self)
        Observer.__init__(self)
        self._args = args
        self._interpreter = interpreter
        self._interpreter.allocate_tensors()
        input_shape = self._interpreter.get_input_details()[0]["shape"]
        tile_w_overlap = 27
        tile_h_overlap = 92
        tile_size = input_shape[1]
        self._tile_config = TileConfig(tile_size, tile_w_overlap, tile_h_overlap)

        self._ssd_labels = read_label_file(self._args.label) if self._args.label else {}

        self._ssd_infer_time_ms = 0
        self._thread = threading.Thread(target=self._detect, daemon=True)

    def start(self):
        self._thread.start()

    def get_id(self):
        return self.__class__.__name__

    def _union_of_interected_objects(self, objects_by_label):
        union_objects_by_label = dict()
        for label, objects in objects_by_label.items():
            objects = union_of_intersected_objects(objects, self._args.iou_threshold)
            union_objects_by_label[label] = objects
        return union_objects_by_label

    def _detect(self):
        for img, image_time in iter(self.get, None):
            logging.debug("recv image from: {}".format(image_time))
            objects = self.detect(img)
            self.publish((objects, img, image_time))

    def detect(self, img):
        inference_time = 0
        objects_by_label = dict()
        for tile_location in tiles_location_gen(img.size, self._tile_config):
            # print(tile_location)
            tile = img.crop(tile_location)
            common.set_input(self._interpreter, tile)
            start = time.perf_counter()
            self._interpreter.invoke()
            inference_time += time.perf_counter() - start
            objs = detect.get_objects(self._interpreter, self._args.score_threshold)
            for obj in objs:
                bbox = [obj.bbox.xmin, obj.bbox.ymin, obj.bbox.xmax, obj.bbox.ymax]
                bbox = reposition_bounding_box(bbox, tile_location)

                label = self._ssd_labels.get(obj.id, "")
                if label == "traffic":  # care about traffic lights for now
                    objects_by_label.setdefault(label, []).append(
                        Object(label, obj.score, bbox)
                    )

        self._ssd_infer_time_ms = inference_time * 1000
        logging.debug("ssd infer time %.2f ms" % (self._ssd_infer_time_ms))

        return self._union_of_interected_objects(objects_by_label)
