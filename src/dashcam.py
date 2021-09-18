import argparse
import logging
import pathlib

import picamera

from .camera_recorder_controller import CameraRecorderController
from .os_utils import generate_recording_postfix
from .camera_recorder import CameraRecorder
from .camera_info import CameraInfo
from .led import ILed
from .speaker import Speaker


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

    parser.add_argument(
        "--record_on_motion",
        action="store_true",
        help="Only record if motion is detected in the scene",
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
        logging.basicConfig(
            filename=str(log_path),
            format="%(asctime)s %(levelname)-6s %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        camera_info = CameraInfo("config/dashcam.yml")
        motion_detection_config = CameraInfo("config/motion_detection_config.yml")

        with picamera.PiCamera() as camera:
            # fps for recording
            camera.framerate = 24
            camera.resolution = camera_info.resolution
            camera.exposure_mode = "sports"
            camera.vflip = args.vflip
            camera.hflip = args.hflip

            camera_recorder = CameraRecorder(
                camera, ILed(), args.blackbox_path, daemon=False
            )
            start_recording = True

            if args.record_on_motion:
                from src.camera_motion_detection import CameraMotionDetection

                camera_motion_detection = CameraMotionDetection(
                    camera, 10, CameraInfo("config/motion_detection_config.yml")
                )
                camera_recorder_controller = CameraRecorderController(camera_recorder)
                camera_motion_detection.add_observer(camera_recorder_controller)
                start_recording = False

            s = Speaker()
            s.play_sound("dashcam")

            camera_recorder.run(start_recording)

    except Exception as e:
        Speaker().play_sound("dead", is_blocking=True)
        logging.critical(str(e))
        print(str(e))
        exit(1)


if __name__ == "__main__":
    main()
