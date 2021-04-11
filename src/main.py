import argparse
from .copilot import CoPilot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--thumbnail_path",
        help="Output path for cropped objects",
        default="/mnt/hdd/detections",
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
    parser.add_argument("--traffic_light_label", help="Labels file path for traffic light model.")

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
    args = parser.parse_args()
    copilot = CoPilot(args)
    copilot.run()


if __name__ == "__main__":
    main()
