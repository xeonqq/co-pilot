import unittest
import numpy as np

from .context import src

from PIL import Image

from src.copilot import CoPilot
from src.utils import draw_objects
from tests.test_fixture import TestFixture

class Args(object):
    pass


class TestDetection(TestFixture):
    def test_detection_with_sample_image(self):
        image = Image.open("tests/traffic_light_scene.jpg", "r")
        image = image.resize(self._camera_info.resolution)

        objects_by_label = self._copilot.detect(image)

        self.assertTrue(len(objects_by_label["traffic"]) >= 2)
        self.assertLess(self._copilot._ssd_infer_time_ms, 1000)

        draw_objects(image, objects_by_label)
        image.save("tests/detection.jpg")


if __name__ == "__main__":
    unittest.main()
