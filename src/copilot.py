import logging
import os
import collections
import time

from PIL import Image

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.adapters import classify
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

# from .button import Button
from .image_saver import AsyncImageSaver
from .utils import (
    crop_objects,
    tiles_location_gen,
    non_max_suppression,
    reposition_bounding_box,
    TileConfig,
    union_of_intersected_objects,
    Object,
)
from .speaker import Speaker, TrafficLightMachine
from .tracker import selected_driving_relevant, Tracker
from .traffic_light import TrafficLight


class CoPilot(object):
    def __init__(self, args, pubsub, blackbox, camera_info, led):
        self._camera_info = camera_info
        assert self._camera_info.resolution == (
            1120,  # 35 * 32, must be multiple of 32
            848,
        )  # 53 * 16, must be multiple of 16
        self._args = args
        self._pubsub = pubsub
        self._blackbox = blackbox

        self._tracker = Tracker(camera_info)
        self._traffic_light_state = TrafficLightMachine()

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
        self._led = led
        self._led.off()

        self._ssd_infer_time_ms = 0
        self._traffic_light_infer_time_ms = 0
        # button_pin = 8
        # button = Button(button_pin)
        self._speaker.play("visibility_clear")
        logging.info("Starting jounery on {}".format(time.strftime("%Y%m%d-%H%M%S")))

    def stop(self):
        self._blackbox.stop_and_join()

    def run(self):
        prev_cycle_time = time.perf_counter()
        for image in iter(self._pubsub.get, None):
            current_cycle_time = time.perf_counter()
            logging.debug(
                "cycle time %.2f ms" % ((current_cycle_time - prev_cycle_time) * 1000)
            )
            prev_cycle_time = current_cycle_time
            self.process(image)

    def _led_on_given(self, objects_by_label, label):
        if label in objects_by_label:
            self._led.on()
        else:
            self._led.off()

    def process(self, image):

        objects_by_label = self.detect(image)
        self._led_on_given(objects_by_label, "traffic")

        traffic_lights = self.classify_traffic_lights(image, objects_by_label)

        driving_relevant_traffic_light = selected_driving_relevant(
            traffic_lights, self._camera_info
        )

        if driving_relevant_traffic_light:
            sound = self._traffic_light_state.update(driving_relevant_traffic_light.cls)
            self._speaker.play(sound)

        self._blackbox.log(image, traffic_lights, objects_by_label)

    def classify_traffic_lights(self, image, objects_by_label):
        detected_traffic_lights = objects_by_label.get("traffic", [])
        object_images = crop_objects(image, detected_traffic_lights)
        traffic_lights = []
        for obj_image, detection in zip(object_images, detected_traffic_lights):
            c, score = self.classify(obj_image)
            traffic_lights.append(TrafficLight(c, score, detection, obj_image))
            # if c:
            #    self._speaker.play(c)
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
            [
                0,
                0,
                self._camera_info.width,
                int(self._camera_info.height * self._h_crop_keep_percentage),
            ]
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
                if label == "traffic":  # care about traffic lights for now
                    objects_by_label.setdefault(label, []).append(
                        Object(label, obj.score, bbox)
                    )

        self._ssd_infer_time_ms = inference_time * 1000
        logging.debug("ssd infer time %.2f ms" % (self._ssd_infer_time_ms))

        return self._union_of_interected_objects(objects_by_label)

    def _non_max_suppress(self, objects_by_label):
        nms_objects_by_label = dict()
        for label, objects in objects_by_label.items():
            idxs = non_max_suppression(objects, self._args.iou_threshold)
            for idx in idxs:
                nms_objects_by_label.setdefault(label, []).append(objects[idx])
        return nms_objects_by_label

    def _union_of_interected_objects(self, objects_by_label):
        union_objects_by_label = dict()
        for label, objects in objects_by_label.items():
            objects = union_of_intersected_objects(objects, self._args.iou_threshold)
            union_objects_by_label[label] = objects
        return union_objects_by_label
