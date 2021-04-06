import picamera
from button import Button
from led import Led
import RPi.GPIO as GPIO

import logging
import io
import os
import argparse
import collections
import time

import numpy as np
from PIL import Image
from PIL import ImageDraw

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

Object = collections.namedtuple("Object", ["label", "score", "bbox"])


logging.basicConfig(
    filename="{}/traffic_light_alert.log".format(os.getcwd()), level=logging.DEBUG
)


def tiles_location_gen(img_size, tile_size, overlaps):
    """Generates location of tiles after splitting the given image according the tile_size and overlap.

    Args:
      img_size (int, int): size of original image as width x height.
      tile_size (int, int): size of the returned tiles as width x height.
      overlap (int): The number of pixels to overlap the tiles.

    Yields:
      A list of points representing the coordinates of the tile in xmin, ymin,
      xmax, ymax.
    """
    img_width, img_height = img_size
    w_stride = tile_size - overlaps[0]
    h_stride = tile_size - overlaps[1]
    pixels_ignore = 5
    for h in range(0, img_height - overlaps[1] - pixels_ignore, h_stride):
        for w in range(0, img_width - overlaps[0] - pixels_ignore, w_stride):
            xmin = w
            ymin = h
            xmax = min(img_width, w + tile_size)
            ymax = min(img_height, h + tile_size)
            yield [xmin, ymin, xmax, ymax]


def non_max_suppression(objects, threshold):
    """Returns a list of indexes of objects passing the NMS.

    Args:
      objects: result candidates.
      threshold: the threshold of overlapping IoU to merge the boxes.

    Returns:
      A list of indexes containings the objects that pass the NMS.
    """
    if len(objects) == 1:
        return [0]

    boxes = np.array([o.bbox for o in objects])
    xmins = boxes[:, 0]
    ymins = boxes[:, 1]
    xmaxs = boxes[:, 2]
    ymaxs = boxes[:, 3]

    areas = (xmaxs - xmins) * (ymaxs - ymins)
    scores = [o.score for o in objects]
    idxs = np.argsort(scores)

    selected_idxs = []
    while idxs.size != 0:

        selected_idx = idxs[-1]
        selected_idxs.append(selected_idx)

        overlapped_xmins = np.maximum(xmins[selected_idx], xmins[idxs[:-1]])
        overlapped_ymins = np.maximum(ymins[selected_idx], ymins[idxs[:-1]])
        overlapped_xmaxs = np.minimum(xmaxs[selected_idx], xmaxs[idxs[:-1]])
        overlapped_ymaxs = np.minimum(ymaxs[selected_idx], ymaxs[idxs[:-1]])

        w = np.maximum(0, overlapped_xmaxs - overlapped_xmins)
        h = np.maximum(0, overlapped_ymaxs - overlapped_ymins)

        intersections = w * h
        unions = areas[idxs[:-1]] + areas[selected_idx] - intersections
        ious = intersections / unions

        idxs = np.delete(
            idxs, np.concatenate(([len(idxs) - 1], np.where(ious > threshold)[0]))
        )

    return selected_idxs


def draw_object(draw, obj):
    """Draws detection candidate on the image.

    Args:
      draw: the PIL.ImageDraw object that draw on the image.
      obj: The detection candidate.
    """
    draw.rectangle(obj.bbox, outline="red")
    draw.text((obj.bbox[0], obj.bbox[3]), obj.label, fill="#0000")
    draw.text((obj.bbox[0], obj.bbox[3] + 10), str(obj.score), fill="#0000")


def reposition_bounding_box(bbox, tile_location):
    """Relocates bbox to the relative location to the original image.

    Args:
      bbox (int, int, int, int): bounding box relative to tile_location as xmin,
        ymin, xmax, ymax.
      tile_location (int, int, int, int): tile_location in the original image as
        xmin, ymin, xmax, ymax.

    Returns:
      A list of points representing the location of the bounding box relative to
      the original image as xmin, ymin, xmax, ymax.
    """
    bbox[0] = bbox[0] + tile_location[0]
    bbox[1] = bbox[1] + tile_location[1]
    bbox[2] = bbox[2] + tile_location[0]
    bbox[3] = bbox[3] + tile_location[1]
    return bbox


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
    args = parser.parse_args()

    width = 1120  # 35 * 32, must be multiple of 32
    height = 848  # 53 * 16, must be multiple of 16
    # resolution = (1280,960)
    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    input_shape = interpreter.get_input_details()[0]["shape"]
    tile_w_overlap = 27
    tile_h_overlap = 92
    tile_size = input_shape[1]

    labels = read_label_file(args.label) if args.label else {}
    # button_pin = 8
    led_pin = 10
    # button = Button(button_pin)
    led = Led(led_pin)
    led.off()
    prev_cycle_time = time.perf_counter()
    with picamera.PiCamera(
        resolution="{}x{}".format(width, height), framerate=24
    ) as camera:
        camera.vflip = True
        stream = io.BytesIO()
        for i, _ in enumerate(
            camera.capture_continuous(stream, format="rgb", use_video_port=True)
        ):
            current_cycle_time = time.perf_counter()
            logging.debug(
                "cycle time %.2f ms" % ((current_cycle_time - prev_cycle_time) * 1000)
            )
            prev_cycle_time = current_cycle_time

            stream.truncate()
            stream.seek(0)
            img_origin = Image.frombuffer("RGB", (width, height), stream.getvalue())
            draw = ImageDraw.Draw(img_origin)
            img = img_origin.crop([0, 0, width, int(height * 0.6)])
            inference_time = 0
            objects_by_label = dict()
            for tile_location in tiles_location_gen(
                img.size, tile_size, (tile_w_overlap, tile_h_overlap)
            ):
                # print(tile_location)
                tile = img.crop(tile_location)
                common.set_input(interpreter, tile)
                start = time.perf_counter()
                interpreter.invoke()
                inference_time += time.perf_counter() - start
                objs = detect.get_objects(interpreter, args.score_threshold)
                for obj in objs:
                    bbox = [obj.bbox.xmin, obj.bbox.ymin, obj.bbox.xmax, obj.bbox.ymax]
                    bbox = reposition_bounding_box(bbox, tile_location)

                    label = labels.get(obj.id, "")
                    objects_by_label.setdefault(label, []).append(
                        Object(label, obj.score, bbox)
                    )

            logging.debug("inference_time %.2f ms" % (inference_time * 1000))
            for label, objects in objects_by_label.items():
                idxs = non_max_suppression(objects, args.iou_threshold)
                for idx in idxs:
                    draw_object(draw, objects[idx])
            if "traffic" in objects_by_label:
                led.on()
            else:
                led.off()

            # img_origin.save("detection{}.bmp".format(i))


if __name__ == "__main__":
    main()
