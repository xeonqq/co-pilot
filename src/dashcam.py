import argparse
import logging
import pathlib

import picamera

from .os_utils import generate_recording_postfix
from .camera_recorder import CameraRecorder
from .camera_info import CameraInfo
from .led import ILed


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--blackbox_path",
        help="Output path for blackbox (images, video)",
        default="/home/pi/dashcam_recording",
    )

    parser.add_argument(
        "--vflip",
        action="store_true",
        help="vflip camera view",
    )
    parser.add_argument(
        "--hflip",
        action="store_true",
        help="hflip camera view",
    )
    return parser.parse_args()


def main():
    try:
        args = parse_arguments()
        args.blackbox_path = pathlib.Path(args.blackbox_path).joinpath(
            generate_recording_postfix(args.blackbox_path)
        )
        args.blackbox_path.mkdir(parents=True, exist_ok=True)

        log_path = args.blackbox_path.joinpath("dashcam.log")
        logging.basicConfig(filename=str(log_path), level=logging.DEBUG)

        camera_info = CameraInfo("config/dashcam.yml")

        with picamera.PiCamera() as camera:
            # fps for recording
            camera.framerate = 24
            camera.resolution = camera_info.resolution
            camera.exposure_mode = "sports"
            camera.vflip = args.vflip
            camera.hflip = args.hflip

            camera_recorder = CameraRecorder(camera, ILed(), args.blackbox_path, daemon=False)
            camera_recorder.run()

    except Exception as e:
        logging.critical(str(e))
        print(str(e))
        exit(1)


if __name__ == "__main__":
    main()
