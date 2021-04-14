import yaml
import numpy as np


class CameraInfo(object):
    def __init__(self, intrinsics_yml):
        with open(intrinsics_yml, "r") as f:
            content = yaml.load(f, Loader=yaml.FullLoader)
            self._resolution = (content["image_width"], content["image_height"])
            self._intrinsics = np.asarray(
                content["camera_matrix"]["data"][:-3]
            ).reshape((2, 3))
            self._f = (
                self._intrinsics[0, 0] + self._intrinsics[1, 1]
            ) / 2  # focal_length_in_pixels
            self._pixel_center = np.asarray(
                [self._intrinsics[0, -1], self._intrinsics[1, -1]]
            )

    @property
    def f(self):
        return self._f

    @property
    def resolution(self):
        return self._resolution

    @property
    def intrinsics(self):
        return self._intrinsics

    @property
    def pixel_center(self):
        return self._pixel_center

    @property
    def width(self):
        return self._resolution[0]

    @property
    def height(self):
        return self.resolution[1]
