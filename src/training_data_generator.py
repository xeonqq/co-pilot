import os
import argparse
import pathlib

from PIL import Image

from .copilot import CoPilot
from .utils import draw_objects


def get_jpgs_in_path(path):
    path_to_test_images_dir = pathlib.Path(path)
    test_image_paths = sorted(list(path_to_test_images_dir.glob("*.jpg")))
    return test_image_paths


def detect_and_extract_objects(args):
    copilot = CoPilot(args)
    input_paths = [input_path for input_path in args.input_paths.split(",")]
    for path in input_paths:
        test_image_paths = get_jpgs_in_path(path)
        for image_path in test_image_paths:
            image = Image.open(image_path, "r")
            image = image.resize((copilot._width, copilot._height))
            objects_by_label = copilot.detect(image)

            name = os.path.basename(image_path)
            name = os.path.splitext(name)[0]
            copilot.save_cropped_objects(image, objects_by_label, ["traffic light"], name)
            draw_objects(image, objects_by_label)
            folder = "{}/detections/".format(args.thumbnail_path)
            pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
            image.save("{}/{}_detection.jpg".format(folder, name))
    copilot.join()


def main():
    parser = argparse.ArgumentParser()
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

    parser.add_argument(
        "--input_paths",
        required=True,
        help="path to images used for extracting objects",
    )
    parser.add_argument("--label_extract", required=True, help="label to extract")
    parser.add_argument(
        "--thumbnail_path",
        help="Output path for cropped objects",
        required=True,
    )
    args = parser.parse_args()
    detect_and_extract_objects(args)


if __name__ == "__main__":
    main()
