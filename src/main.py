import argparse
import logging
import pathlib
import time
import threading

from picamera2 import Picamera2

from src.os_utils import generate_recording_postfix
from .abc import ILed as Led
from .abc import ISpeaker as Speaker
from .camera_capturer import CameraCapturer
from .camera_recorder import CameraRecorder
from .pubsub import PubSub
from .camera_info import CameraInfo
from .inference_config import InferenceConfig
from .copilot import CoPilot
from .image_saver import AsyncImageSaver
from .blackbox import BlackBox
#from .speaker import Speaker
from .utils import run_periodic
from .disk_manager import DiskManager

def make_interpreter(model_path):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        help="select 'full' (full alert mode) or 'minimal' (yellow alert)",
        default='minimal'
    )
    parser.add_argument(
        "--lang",
        help="co-pilot voice language 'en' or 'cn'",
        default="en",
    )
    parser.add_argument(
        "--blackbox_path",
        help="Output path for blackbox (images, detections, video)",
        default="/mnt/hdd",
    )
    parser.add_argument(
        "--ssd_model",
        required=True,
        help="Detection SSD model path (must have post-processing operator).",
    )
    parser.add_argument(
        "--traffic_light_classification_model",
        required=True,
        help="Traffic Light Classification model path",
    )
    parser.add_argument("--label", help="Labels file path for SSD model.")
    parser.add_argument(
        "--traffic_light_label", help="Labels file path for traffic light model."
    )

    parser.add_argument(
        "--score_threshold",
        help="Threshold for returning the candidates.",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--traffic_light_classification_threshold",
        help="Threshold for classify as traffic light",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--iou_threshold",
        help=("threshold to merge bounding box duing nms"),
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="use cpu instead of tpu (default)",
    )

    return parser.parse_args()


def main():
    try:
        args = parse_arguments()

        recording_root = args.blackbox_path

        args.blackbox_path = pathlib.Path(args.blackbox_path).joinpath(
            generate_recording_postfix(args.blackbox_path)
        )
        args.blackbox_path.mkdir(parents=True, exist_ok=True)

        log_path = args.blackbox_path.joinpath("co-pilot.log")
        logging.basicConfig(
            filename=str(log_path),
            format="%(asctime)s %(levelname)-6s %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        disk_manager = DiskManager(recording_root, 100 * 1024 * 1024)
        run_periodic(disk_manager.check_and_delete_old_files)

        camera_info = CameraInfo("config/intrinsics.yml")
        inference_config = InferenceConfig("config/inference_config.yml")
        pubsub = PubSub()
        image_saver = AsyncImageSaver(args.blackbox_path)

        blackbox = BlackBox(image_saver)

        camera = Picamera2()

        main_stream = {"size": camera_info.resolution}
        lores_stream = {"size": inference_config.inference_resolution, "format": "RGB888"}
        video_config = camera.create_video_configuration(main_stream, lores_stream, encode="main")
        camera.configure(video_config)
        fps = 20.0
        camera.set_controls({"FrameRate": fps, "ExposureTime": 20000})

        #metadata = camera.capture_metadata()

        #print("here 4")
        #framerate = 1000000 / metadata["FrameDuration"]
        #print("here 5")

        #logging.debug("configure camera done, fps: {}".format(framerate))


        #camera.framerate = 20
        #camera.exposure_mode = "sports"

        led_pin = 10
        led = Led()
        camera_recorder = CameraRecorder(camera, fps, led, args.blackbox_path)
        camera_capturer = CameraCapturer(
            camera, 5, camera_recorder.is_recording, pubsub, inference_config
        )

        if args.cpu:
            #from tflite_runtime.interpreter import Interpreter as make_interpreter
            pass
        else:
            #from pycoral.utils.edgetpu import make_interpreter
            pass

        try:
            copilot = CoPilot(
                args,
                pubsub,
                blackbox,
                camera_info,
                inference_config,
                led,
                Speaker(args.lang),
                make_interpreter(args.ssd_model),
                make_interpreter(args.traffic_light_classification_model),
            )
        except ValueError as e:
            print(str(e) + "Use --cpu if you do not have a coral tpu")
            return
        copilot.run()

    except Exception as e:
        # Speaker(args.lang).play_sound("dead", is_blocking=True)
        logging.critical(str(e))
        print(str(e))
        exit(1)


if __name__ == "__main__":
    main()
