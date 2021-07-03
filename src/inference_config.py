import yaml
import numpy as np


class InferenceConfig(object):
    def __init__(self, inference_config):
        with open(inference_config, "r") as f:
            content = yaml.load(f, Loader=yaml.FullLoader)
            self._inference_resolution = (
                content["infer_image_width"],
                content["infer_image_height"],
            )

            self._tile_size = content["tile_size"]

            self._tile_w_overlap = content["tile_w_overlap"]
            self._tile_h_overlap = content["tile_h_overlap"]

            self._pixel_center = np.asarray(
                [self._inference_resolution[0] / 2, self._inference_resolution[1] / 2]
            )

    @property
    def inference_resolution(self):
        return self._inference_resolution

    @property
    def tile_size(self):
        return self._tile_size

    @property
    def tile_overlap(self):
        return (self._tile_w_overlap, self._tile_h_overlap)

    @property
    def pixel_center(self):
        return self._pixel_center
