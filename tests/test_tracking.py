import unittest

from .context import src

from src.utils import draw_objects, image_gen
from tests.test_fixture import TestFixture


class Args(object):
    pass


class TestTrafficLightTracking(TestFixture):
    def test_tracking_with_sample_images(self):

        for image in image_gen("tests/test_imgs/tracking", self._camera_info):
            self._copilot.process(image)
        self._copilot.stop()


if __name__ == "__main__":
    unittest.main()
