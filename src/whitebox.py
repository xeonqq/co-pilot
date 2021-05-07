from .utils import draw_objects_and_traffic_lights, draw_traffic_light_tracks
import cv2
import numpy as np


class WhiteBox(object):
    def __init__(self, image_saver, enable_step):
        self._image_saver = image_saver
        self._enable_step = enable_step

    def log(self, image, traffic_lights, objects_by_label, tracker):
        # save image with detection overlay,
        # as well as cropped detection and classification result
        # draw_objects_and_traffic_lights(image, objects_by_label, traffic_lights)
        draw_traffic_light_tracks(image, tracker)
        if traffic_lights:
            self._image_saver.save_image_and_traffic_lights(image, traffic_lights)
        imcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

        cv2.imshow("display", imcv)
        ms = 0 if self._enable_step else 200
        cv2.waitKey(ms)

    def stop_and_join(self):
        self._image_saver.stop_and_join()
