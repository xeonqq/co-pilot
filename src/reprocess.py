import os
import time
import argparse
import pathlib
from videoio import VideoReader
from PIL import Image

from .copilot import CoPilot
from .pubsub import PubSub
from .camera_info import CameraInfo
from .whitebox import WhiteBox
from .image_saver import AsyncImageSaver

class LedMock(object):
    def on(self):
        pass
    
    def off(self):
        pass

    def toggle(self):
        pass

def reprocess(args):

    pubsub = PubSub()
    camera_info = CameraInfo("config/intrinsics.yml")
    image_saver = AsyncImageSaver(args.blackbox_path)
    whitebox = WhiteBox(image_saver)
    copilot = CoPilot(args, pubsub, whitebox, camera_info, LedMock())

    for frame in VideoReader(args.video):
        image = Image.fromarray(frame)
        image = image.transpose(method=Image.FLIP_TOP_BOTTOM)
        copilot.process(image)
        #if args.real_time:
        #    time.sleep(0.05)
    copilot.join()


def parse_arguments():
    parser = argparse.ArgumentParser()
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
        "--video",
        required=True,
        help="path to the video to be reprocessed",
    )

    parser.add_argument(
        "--real_time",
        action="store_true",
        help="use real time reprocessing",
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    args.blackbox_path = pathlib.Path(args.blackbox_path).joinpath(
                time.strftime("%Y%m%d-%H%M%S")
    )
    reprocess(args)


if __name__ == "__main__":
    main()
