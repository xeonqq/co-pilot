import unittest
import time
import pathlib
import numpy as np

from .context import src

from PIL import Image

from src.copilot import CoPilot
from src.utils import draw_objects, image_gen
from src.camera_info import CameraInfo
from src.abc import ILed
from src.image_saver import AsyncImageSaver
from src.blackbox import BlackBox


class Args(object):
    pass


class TestTrafficLightTracking(unittest.TestCase):
    def test_tracking_with_sample_images(self):
        args = Args()
        args.label = "models/coco_labels.txt"
        args.ssd_model = "models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite"
        args.score_threshold = 0.3
        args.iou_threshold = 0.1

        args.traffic_light_classification_model = "models/traffic_light_edgetpu.tflite"
        args.traffic_light_label = "models/traffic_light_labels.txt"
        args.traffic_light_classification_threshold = 0.5

        camera_info = CameraInfo("config/intrinsics.yml")

        args.blackbox_path = pathlib.Path("tests/tracking_test_artifacts").joinpath(
            time.strftime("%Y%m%d-%H%M%S")
        )
        args.blackbox_path.mkdir(parents=True, exist_ok=True)
        image_saver = AsyncImageSaver(args.blackbox_path)
        blackbox = BlackBox(image_saver)

        copilot = CoPilot(args, None, blackbox, camera_info, ILed())

        for image in image_gen("tests/test_imgs/tracking", camera_info):
            copilot.process(image)



if __name__ == "__main__":
    unittest.main()
