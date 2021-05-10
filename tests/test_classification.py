import unittest

from PIL import Image

from tests.test_fixture import TestFixture


class Args(object):
    pass


class TestTrafficLightClassification(TestFixture):
    def test_classication_with_sample_image(self):

        image = Image.open("tests/traffic_light.bmp", "r")

        image = image.resize(self._copilot._traffic_light_size, Image.ANTIALIAS)

        c, score = self._copilot.classify(image)

        self.assertEqual(c, "red")
        self.assertGreater(score, 0.6)
        self.assertLess(self._copilot._traffic_light_infer_time_ms, 1)


if __name__ == "__main__":
    unittest.main()
