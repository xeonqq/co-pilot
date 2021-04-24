import os
import logging
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
from .abc import ILed


def get_image_gen(args, camera_info):

    if args.video:
        default_fps = 20
        for i, frame in enumerate(VideoReader(args.video)):
            if args.fps and i%(default_fps//args.fps) != 0:
                continue

            image = Image.fromarray(frame)
            if args.flip:
                image = image.transpose(method=Image.FLIP_TOP_BOTTOM)
            image = image.resize(camera_info.resolution)
            yield image

    if args.images:
        path_to_test_images = pathlib.Path(args.images)
        image_paths = sorted(list(path_to_test_images.glob("*.jpg")))
        for image_path in image_paths:
            image = Image.open(image_path, "r").convert("RGB")
            image = image.resize(camera_info.resolution)
            yield image
    else:
        assert "must provide --video or --images"


def reprocess(args):

    pubsub = PubSub()
    camera_info = CameraInfo("config/intrinsics.yml")
    image_saver = AsyncImageSaver(args.blackbox_path)
    whitebox = WhiteBox(image_saver)
    copilot = CoPilot(args, pubsub, whitebox, camera_info, ILed())

    for image in get_image_gen(args, camera_info):
        copilot.process(image)
        # if args.real_time:
        #    time.sleep(0.05)
    copilot.stop()


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
        "--fps",
        help=("frame rate to play the video"),
        type=int,
        default=None,
    )

    parser.add_argument(
        "--video",
        help="path to the video to be reprocessed",
    )

    parser.add_argument(
        "--images",
        help="path to the folder of images to be reprocessed",
    )

    parser.add_argument(
        "--flip",
        action="store_true",
        help="flip top bottom of the video",
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
    args.blackbox_path.mkdir(parents=True, exist_ok=True)
    log_path = args.blackbox_path.joinpath("co-pilot.log")
    logging.basicConfig(filename=str(log_path), level=logging.DEBUG)
    reprocess(args)


if __name__ == "__main__":
    main()
