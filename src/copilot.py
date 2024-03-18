import logging
import time

from PIL import Image

from .adapters import common,detect,classify
# from pycoral.adapters import 
# from pycoral.adapters import classify
# from pycoral.utils.dataset import read_label_file

# from .button import Button
import numpy as np
from .utils import (
        crop_objects,
        tiles_location_gen,
        non_max_suppression,
        reposition_bounding_box,
        TileConfig,
        union_of_intersected_objects,
        read_label_file,
        Object,
        )
# from .traffic_light_state_adaptor import TrafficLightStateAdaptor
from .state_machine import TrafficLightStateAdaptorWithSM as TrafficLightStateAdaptor
from .tracker import selected_driving_relevant, Tracker
from .traffic_light import TrafficLight


class CoPilot(object):
    def __init__(
            self,
            args,
            pubsub,
            blackbox,
        camera_info,
        inference_config,
        led,
        speaker,
        ssd_interpreter,
        traffic_light_classifier_interpreter,
    ):
        self._camera_info = camera_info
        self._inference_config = inference_config

        assert self._camera_info.resolution == (
            1120,  # 35 * 32, must be multiple of 32
            624,
        )  # Y * 16, must be multiple of 16
        self._args = args
        self._pubsub = pubsub
        self._blackbox = blackbox

        self._tracker = Tracker(inference_config)
        self._traffic_light_state = TrafficLightStateAdaptor(args.mode)

        self._ssd_interpreter = ssd_interpreter
        self._ssd_interpreter.allocate_tensors()

        self._classfication_interpreter = traffic_light_classifier_interpreter
        self._classfication_interpreter.allocate_tensors()
        self._traffic_light_size = common.input_size(self._classfication_interpreter)

        self._speaker = speaker

        input_shape = self._ssd_interpreter.get_input_details()[0]["shape"]
        tile_w_overlap, tile_h_overlap = self._inference_config.tile_overlap
        tile_size = self._inference_config.tile_size
        assert tile_size == input_shape[1]
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
        self._speaker.play_ready(args.mode)
        logging.info("Starting jounery on {}".format(time.strftime("%Y%m%d-%H%M%S")))

    def stop(self):
        self._blackbox.stop_and_join()

    def run(self):
        prev_cycle_time = time.perf_counter()
        for image, image_time in iter(self._pubsub.get, None):
            current_cycle_time = time.perf_counter()
            # logging.debug("image time diff: %.2f ms" % ((current_cycle_time-image_time)*1000))
            logging.debug(
                "cycle time %.2f ms" % ((current_cycle_time - prev_cycle_time) * 1000)
            )
            prev_cycle_time = current_cycle_time
            logging.debug("recv image from: {}".format(image_time))
            self.process(image)
            # self._blackbox.log_image(image)
            
            logging.debug(
                "process time: %.2f ms"
                % ((time.perf_counter() - current_cycle_time) * 1000)
            )

    def _led_on_given(self, objects_by_label, label):
        if label in objects_by_label:
            self._led.on()
        else:
            self._led.off()

    def process(self, image):

        objects_by_label = self.detect(image)
        self._led_on_given(objects_by_label, "traffic light")

        traffic_lights = self.classify_traffic_lights(image, objects_by_label)

        self._tracker.track(traffic_lights)
        relevant_traffic_light_track = self._tracker.get_driving_relevant_track()
        traffic_light_cls = (
            relevant_traffic_light_track.cls if relevant_traffic_light_track else None
        )

        sound = self._traffic_light_state.update(traffic_light_cls)
        self._speaker.play(sound)

        self._blackbox.log(image, traffic_lights, objects_by_label, self._tracker)

    def classify_traffic_lights(self, image, objects_by_label):
        detected_traffic_lights = objects_by_label.get("traffic light", [])
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

    def detect(self, img):
        inference_time = 0
        objects_by_label = dict()
        # img = image.crop(
        #        [
        #            0,
        #            0,
        #            self._inference_config.inference_resolution[0],
        #            self._inference_config.inference_resolution[1]
        #            ]
        #        )

        for tile_location in tiles_location_gen(
            self._inference_config.inference_resolution, self._tile_config
        ):
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
                if label == "traffic light":  # care about traffic lights for now
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
