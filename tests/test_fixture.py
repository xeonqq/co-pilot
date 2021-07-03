import unittest
import pathlib
from PIL import Image

from src.copilot import CoPilot
from src.camera_info import CameraInfo
from src.abc import ILed, IBlackBox, ISpeaker
from src.inference_config import InferenceConfig


class Args(object):
    pass


class TestFixture(unittest.TestCase):
    def setUp(self):
        use_cpu = True
        args = Args()
        args.label = "models/coco_labels.txt"
        args.score_threshold = 0.3
        args.iou_threshold = 0.1

        args.traffic_light_label = "models/traffic_light_labels.txt"
        args.traffic_light_classification_threshold = 0.5

        self._camera_info = CameraInfo("config/intrinsics.yml")
        self._inference_config = InferenceConfig("config/inference_config.yml")

        if use_cpu:
            from tflite_runtime.interpreter import Interpreter as make_interpreter

            args.traffic_light_classification_model = "models/host/traffic_light.tflite"
            args.ssd_model = "models/host/ssd_mobilenet_v2_coco_quant_no_nms.tflite"
        else:
            from pycoral.utils.edgetpu import make_interpreter

            args.traffic_light_classification_model = (
                "models/traffic_light_edgetpu.tflite"
            )
            args.ssd_model = "models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite"

        self._copilot = CoPilot(
            args,
            None,
            IBlackBox(),
            self._camera_info,
            self._inference_config,
            ILed(),
            ISpeaker(),
            make_interpreter(args.ssd_model),
            make_interpreter(args.traffic_light_classification_model),
        )

    def resize_image_to_inference_resolution(self, image):
        inference_w, inference_h = self._inference_config.inference_resolution
        box = (0, 0, image.size[0], min(image.size[0] * inference_h / inference_w, image.size[1]))
        return image.resize(self._inference_config.inference_resolution, box=box)

    def image_gen(self, image_folder_path):
        path_to_test_images = pathlib.Path(image_folder_path)
        image_paths = sorted(list(path_to_test_images.glob("*.jpg")))
        for image_path in image_paths:
            image = Image.open(image_path, "r").convert("RGB")
            yield self.resize_image_to_inference_resolution(image)
