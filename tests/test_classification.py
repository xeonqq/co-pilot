import unittest
import numpy as np

from .context import src

from PIL import Image

from src.copilot import CoPilot
from src.utils import draw_objects
from src.camera_info import CameraInfo
from src.abc import ILed


class Args(object):
    pass


class TestTrafficLightClassification(unittest.TestCase):
    def test_classication_with_sample_image(self):
        args = Args()
        args.label = "models/coco_labels.txt"
        args.ssd_model = "models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite"

        args.traffic_light_classification_model = "models/traffic_light_edgetpu.tflite"
        args.traffic_light_label = "models/traffic_light_labels.txt"
        args.traffic_light_classification_threshold = 0.5

        camera_info = CameraInfo("config/intrinsics.yml")

        copilot = CoPilot(args, None, None, camera_info, ILed())

        image = Image.open("tests/traffic_light.bmp", "r")

        image = image.resize(copilot._traffic_light_size, Image.ANTIALIAS)

        c, score = copilot.classify(image)

        self.assertEqual(c, "red")
        self.assertGreater(score, 0.6)
        self.assertLess(copilot._traffic_light_infer_time_ms, 1)


if __name__ == "__main__":
    unittest.main()
