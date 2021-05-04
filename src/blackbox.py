from .utils import (
    draw_objects_and_traffic_lights
)


class BlackBox(object):
    def __init__(self, image_saver):
        self._image_saver = image_saver

    def log(self, image, traffic_lights, objects_by_label, traffic_light_tracks):

        # save image with detection overlay,
        # as well as cropped detection and classification result
        if traffic_lights:
            draw_objects_and_traffic_lights(image, objects_by_label, traffic_lights)
            self._image_saver.save_image_and_traffic_lights(image, traffic_lights)

    def stop_and_join(self):
        self._image_saver.stop_and_join()
