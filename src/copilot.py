import logging
import io
import os
import collections
import time

import picamera
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

from .button import Button
from .led import Led
from .image_saver import AsyncImageSaver
from .utils import (
    tiles_location_gen,
    non_max_suppression,
    draw_objects,
    reposition_bounding_box,
    TileConfig,
)


Object = collections.namedtuple("Object", ["label", "score", "bbox"])


logging.basicConfig(filename="{}/co-pilot.log".format(os.getcwd()), level=logging.DEBUG)


class CoPilot(object):
    def __init__(self, args):
        self._args = args
        self._width = 1120  # 35 * 32, must be multiple of 32
        self._height = 848  # 53 * 16, must be multiple of 16
        # resolution = (1280,960)
        self._interpreter = make_interpreter(self._args.model)
        self._interpreter.allocate_tensors()

        input_shape = self._interpreter.get_input_details()[0]["shape"]
        tile_w_overlap = 27
        tile_h_overlap = 92
        tile_size = input_shape[1]
        self._tile_config = TileConfig(tile_size, tile_w_overlap, tile_h_overlap)

        self._labels = read_label_file(self._args.label) if self._args.label else {}

        self._h_crop_keep_percentage = 0.6
        led_pin = 10
        self._led = Led(led_pin)
        self._led.off()

        self._image_saver = AsyncImageSaver("/mnt/hdd/detections")
        self._inference_time_ms = 0
        # button_pin = 8
        # button = Button(button_pin)

    def run(self):
        prev_cycle_time = time.perf_counter()
        with picamera.PiCamera(
            resolution="{}x{}".format(self._width, self._height), framerate=24
        ) as camera:
            camera.vflip = True
            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                stream, format="rgb", use_video_port=True
            ):
                current_cycle_time = time.perf_counter()
                logging.debug(
                    "cycle time %.2f ms"
                    % ((current_cycle_time - prev_cycle_time) * 1000)
                )
                prev_cycle_time = current_cycle_time

                stream.truncate()
                stream.seek(0)
                img = Image.frombuffer(
                    "RGB", (self._width, self._height), stream.getvalue()
                )
                self.process(img)

    def process(self, image):
        objects_by_label = self.detect(image)
        self._led.on() if "traffic" in objects_by_label else self._led.off()
        self.save_cropped_objects(image, objects_by_label, ["traffic"])
        # self.draw_objects(image, objects_by_label)

    def detect(self, image):
        img = image.crop(
            [0, 0, self._width, int(self._height * self._h_crop_keep_percentage)]
        )

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

                label = self._labels.get(obj.id, "")
                objects_by_label.setdefault(label, []).append(
                    Object(label, obj.score, bbox)
                )

        self._inference_time_ms = inference_time * 1000
        logging.debug("inference_time %.2f ms" % (self._inference_time_ms))

        return self._non_max_suppress(objects_by_label)

    def _non_max_suppress(self, objects_by_label):
        nms_objects_by_label = dict()
        for label, objects in objects_by_label.items():
            idxs = non_max_suppression(objects, self._args.iou_threshold)
            for idx in idxs:
                nms_objects_by_label.setdefault(label, []).append(objects[idx])
        return nms_objects_by_label

    def save_cropped_objects(self, image, objects_by_label, labels_to_save):
        for label in labels_to_save:
            if label in objects_by_label:
                for obj in objects_by_label[label]:
                    self._image_saver.save_object(image, obj)

        # image.save("detection{}.bmp".format(i))
