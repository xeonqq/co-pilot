import unittest

from .context import src

from tests.test_fixture import TestFixture


class Args(object):
    pass


class TestTrafficLightTracking(TestFixture):
    def test_tracking_with_sample_images(self):
        for image in self.image_gen("tests/test_imgs/tracking"):
            self._copilot.process(image)
        self._copilot.stop()


if __name__ == "__main__":
    unittest.main()
