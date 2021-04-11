import unittest
import numpy as np

from .context import src

from PIL import Image

from src.copilot import CoPilot
from src.utils import draw_objects


class Args(object):
    pass


class TestDetection(unittest.TestCase):
    def test_detection_with_sample_image(self):
        args = Args()
        args.label = "models/coco_labels.txt"
        args.ssd_model = "models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite"
        args.iou_threshold = 0.1
        args.score_threshold = 0.4
        args.thumbnail_path= "."

        args.traffic_light_classification_model="models/traffic_light_edgetpu.tflite"
        args.traffic_light_label = "models/traffic_light_labels.txt"
        copilot = CoPilot(args)

        image = Image.open("tests/traffic_light_scene.jpg", "r")
        image = image.resize((copilot._width, copilot._height))

        objects_by_label = copilot.detect(image)

        self.assertTrue(len(objects_by_label["traffic"]) >= 2)
        self.assertTrue(len(objects_by_label["car"]) >= 2)
        self.assertLess(copilot._ssd_infer_time_ms, 1000)

        draw_objects(image, objects_by_label)
        image.save("tests/detection.jpg")


if __name__ == "__main__":
    unittest.main()
