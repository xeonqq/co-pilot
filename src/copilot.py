import logging
import os
import collections
import time
import queue
import pathlib

import picamera
from PIL import Image

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.adapters import classify
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

# from .button import Button
from .led import Led
from .image_saver import AsyncImageSaver
from .utils import (
    crop_objects,
    tiles_location_gen,
    non_max_suppression,
    reposition_bounding_box,
    TileConfig,
    #    draw_objects,
)
from .speaker import Speaker
from .camera_recorder import CameraRecorder
from .camera_capturer import CameraCapturer


Object = collections.namedtuple("Object", ["label", "score", "bbox"])
TrafficLight = collections.namedtuple("TrafficLight", ["cls", "score", "obj", "image"])


logging.basicConfig(filename="{}/co-pilot.log".format(os.getcwd()), level=logging.DEBUG)


class CoPilot(object):
    def __init__(self, args):
        self._args = args
        self._width = 1120  # 35 * 32, must be multiple of 32
        self._height = 848  # 53 * 16, must be multiple of 16

        # resolution = (1280,960)
        self._ssd_interpreter = make_interpreter(self._args.ssd_model)
        self._ssd_interpreter.allocate_tensors()

        self._classfication_interpreter = make_interpreter(
            self._args.traffic_light_classification_model
        )
        self._classfication_interpreter.allocate_tensors()
        self._traffic_light_size = common.input_size(self._classfication_interpreter)

        self._speaker = Speaker()

        input_shape = self._ssd_interpreter.get_input_details()[0]["shape"]
        tile_w_overlap = 27
        tile_h_overlap = 92
        tile_size = input_shape[1]
        self._tile_config = TileConfig(tile_size, tile_w_overlap, tile_h_overlap)

        self._ssd_labels = read_label_file(self._args.label) if self._args.label else {}
        self._traffic_light_labels = (
            read_label_file(self._args.traffic_light_label)
            if self._args.traffic_light_label
            else {}
        )

        self._h_crop_keep_percentage = 0.6
        led_pin = 10
        self._led = Led(led_pin)
        self._led.off()

        self._blackbox_folder = pathlib.Path("/mnt/hdd").joinpath(
            time.strftime("%Y%m%d-%H%M%S")
        )
        self._image_saver = AsyncImageSaver(args.thumbnail_path, self._blackbox_folder)

        self._images = queue.Queue(1)
        self._camera = picamera.PiCamera()
        self._camera.resolution = (self._width, self._height)

        # fps for recording
        self._camera.framerate = 20
        self._camera.vflip = True

        self._camera_recorder = CameraRecorder(
            self._camera, self._led, self._blackbox_folder
        )
        self._camera_capturer = CameraCapturer(
            self._camera, 5, self._camera_recorder.is_recording, self._images
        )

        self._ssd_infer_time_ms = 0
        self._traffic_light_infer_time_ms = 0
        # button_pin = 8
        # button = Button(button_pin)
        self._speaker.play("ready")
        logging.info("Starting jounery on {}".format(time.strftime("%Y%m%d-%H%M%S")))

    def join(self):
        self._image_saver.join()

    def run(self):
        prev_cycle_time = time.perf_counter()
        for image in iter(self._images.get, None):
            current_cycle_time = time.perf_counter()
            logging.debug(
                "cycle time %.2f ms" % ((current_cycle_time - prev_cycle_time) * 1000)
            )
            prev_cycle_time = current_cycle_time
            self.process(image)

    def led_on_given(self, objects_by_label, label):
        if label in objects_by_label:
            self._led.on()
        else:
            self._led.off()

    def process(self, image):
        # collect data
        # self._image_saver.save(image)

        objects_by_label = self.detect(image)
        self.led_on_given(objects_by_label, "traffic")

        traffic_lights = self.classify_traffic_lights(image, objects_by_label)

        # save detection and classification result
        self._image_saver.save_traffic_lights(traffic_lights)
        # draw_objects(image, objects_by_label)

    def classify_traffic_lights(self, image, objects_by_label):
        detected_traffic_lights = objects_by_label.get("traffic", [])
        object_images = crop_objects(image, detected_traffic_lights)
        traffic_lights = []
        for obj_image, detection in zip(object_images, detected_traffic_lights):
            c, score = self.classify(obj_image)
            traffic_lights.append(TrafficLight(c, score, detection, obj_image))
            if c:
                self._speaker.play(c)
        return traffic_lights

    def classify(self, traffic_light_thumbnail):
        traffic_light_resized = traffic_light_thumbnail.resize(
            self._traffic_light_size, Image.ANTIALIAS
        )
        common.set_input(self._classfication_interpreter, traffic_light_resized)
        start = time.perf_counter()
        self._classfication_interpreter.invoke()
        classes = classify.get_classes(
            self._classfication_interpreter,
            1,
            self._args.traffic_light_classification_threshold,
        )
        classification_result = (None, 0)
        for c in classes:
            label = self._traffic_light_labels.get(c.id, c.id)
            logging.debug("%s: %.5f" % (label, c.score))
            classification_result = (label, c.score)

        self._traffic_light_infer_time_ms = time.perf_counter() - start
        logging.debug(
            "classification time %.2f ms" % (self._traffic_light_infer_time_ms)
        )
        return classification_result

    def detect(self, image):
        img = image.crop(
            [0, 0, self._width, int(self._height * self._h_crop_keep_percentage)]
        )

        inference_time = 0
        objects_by_label = dict()
        for tile_location in tiles_location_gen(img.size, self._tile_config):
            # print(tile_location)
            tile = img.crop(tile_location)
            common.set_input(self._ssd_interpreter, tile)
            start = time.perf_counter()
            self._ssd_interpreter.invoke()
            inference_time += time.perf_counter() - start
            objs = detect.get_objects(self._ssd_interpreter, self._args.score_threshold)
            for obj in objs:
                bbox = [obj.bbox.xmin, obj.bbox.ymin, obj.bbox.xmax, obj.bbox.ymax]
                bbox = reposition_bounding_box(bbox, tile_location)

                label = self._ssd_labels.get(obj.id, "")
                objects_by_label.setdefault(label, []).append(
                    Object(label, obj.score, bbox)
                )

        self._ssd_infer_time_ms = inference_time * 1000
        logging.debug("ssd infer time %.2f ms" % (self._ssd_infer_time_ms))

        return self._non_max_suppress(objects_by_label)

    def _non_max_suppress(self, objects_by_label):
        nms_objects_by_label = dict()
        for label, objects in objects_by_label.items():
            idxs = non_max_suppression(objects, self._args.iou_threshold)
            for idx in idxs:
                nms_objects_by_label.setdefault(label, []).append(objects[idx])
        return nms_objects_by_label

    def save_cropped_objects(self, object_images, name=""):
        for obj in object_images:
            self._image_saver.save_object(obj, name)

        # image.save("detection{}.bmp".format(i))
