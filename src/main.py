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
        "--model",
        required=True,
        help="Detection SSD model path (must have post-processing operator).",
    )
    parser.add_argument("--label", help="Labels file path.")
    parser.add_argument(
        "--score_threshold",
        help="Threshold for returning the candidates.",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--tile_overlap",
        help=(
            "Number of pixels to overlap the tiles. tile_overlap should be >= "
            "than half of the min desired object size, otherwise small objects "
            "could be missed on the tile boundary."
        ),
        type=int,
        default=15,
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
