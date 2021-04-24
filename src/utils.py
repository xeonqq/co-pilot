import collections
import pathlib
import numpy as np

from PIL import ImageDraw, Image

TileConfig = collections.namedtuple(
    "TileConfig", ["tile_size", "tile_w_overlap", "tile_h_overlap"]
)
Object = collections.namedtuple("Object", ["label", "score", "bbox"])

RED_STATES = {"red", "red_left", "red_right"}
GREEN_STATES = {"green", "green_left", "green_right"}


def is_red(state):
    return state in RED_STATES

def is_green(state):
    return state in GREEN_STATES

def tiles_location_gen(img_size, tile_config):
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
    w_stride = tile_config.tile_size - tile_config.tile_w_overlap
    h_stride = tile_config.tile_size - tile_config.tile_h_overlap

    pixels_ignore = 5
    for h in range(
        0, img_height - tile_config.tile_h_overlap - pixels_ignore, h_stride
    ):
        for w in range(
            0, img_width - tile_config.tile_w_overlap - pixels_ignore, w_stride
        ):
            xmin = w
            ymin = h
            xmax = min(img_width, w + tile_config.tile_size)
            ymax = min(img_height, h + tile_config.tile_size)
            yield [xmin, ymin, xmax, ymax]


def union_of_intersected_objects(objects, threshold):
    if len(objects) == 1:
        return objects

    union_of_objects = []
    boxes = np.array([o.bbox for o in objects])
    xmins = boxes[:, 0]
    ymins = boxes[:, 1]
    xmaxs = boxes[:, 2]
    ymaxs = boxes[:, 3]

    areas = (xmaxs - xmins) * (ymaxs - ymins)
    scores = [o.score for o in objects]
    idxs = np.argsort(scores)

    while idxs.size != 0:

        selected_idx = idxs[-1]
        max_prob_object = objects[selected_idx]

        overlapped_xmins = np.maximum(xmins[selected_idx], xmins[idxs[:-1]])
        overlapped_ymins = np.maximum(ymins[selected_idx], ymins[idxs[:-1]])
        overlapped_xmaxs = np.minimum(xmaxs[selected_idx], xmaxs[idxs[:-1]])
        overlapped_ymaxs = np.minimum(ymaxs[selected_idx], ymaxs[idxs[:-1]])

        w = np.maximum(0, overlapped_xmaxs - overlapped_xmins)
        h = np.maximum(0, overlapped_ymaxs - overlapped_ymins)

        intersections = w * h
        unions = areas[idxs[:-1]] + areas[selected_idx] - intersections
        ious = intersections / unions

        sub_idxs_intersected = np.concatenate(
            ([len(idxs) - 1], np.where(ious > threshold)[0])
        )

        union_xmin = xmins[idxs[sub_idxs_intersected]].min()
        union_ymin = ymins[idxs[sub_idxs_intersected]].min()
        union_xmax = xmaxs[idxs[sub_idxs_intersected]].max()
        union_ymax = ymaxs[idxs[sub_idxs_intersected]].max()

        idxs = np.delete(idxs, sub_idxs_intersected)

        union_of_objects.append(
            Object(
                max_prob_object.label,
                max_prob_object.score,
                [union_xmin, union_ymin, union_xmax, union_ymax],
            )
        )

    return union_of_objects


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


def draw_objects(image, objects_by_label):
    draw = ImageDraw.Draw(image)
    for label, objects in objects_by_label.items():
        for obj in objects:
            draw_object(draw, obj)

def _get_traffic_light_drawing_color(traffic_light):
    color_map ={"green": "#00ff00",
                "red": "#ff0000",
                "yellow": "#FFFF00",
                "red_yellow": "#FFA500",
                "green_left": "#008000",
                "red_left": "#CD5C5C",
                "green_right": "#006400",
                "red_right": "#8B0000",
                }
    return color_map.get(traffic_light.cls, "white")

def draw_traffic_light(draw, traffic_light):
    """Draws detection candidate on the image.

    Args:
      draw: the PIL.ImageDraw object that draw on the image.
      traffic_light: traffic light with classification
    """
    if not traffic_light.cls:
        return
    color = _get_traffic_light_drawing_color(traffic_light)
    draw.rectangle(traffic_light.obj.bbox, outline=color)
    draw.text((traffic_light.obj.bbox[0], traffic_light.obj.bbox[3]+15), traffic_light.cls, fill=color)
    draw.text((traffic_light.obj.bbox[0], traffic_light.obj.bbox[3] + 25), str(traffic_light.score), fill=color)


def draw_traffic_lights(image, traffic_lights):
    draw = ImageDraw.Draw(image)
    for traffic_light in traffic_lights:
        draw_traffic_light(draw, traffic_light)

def draw_objects_and_traffic_lights(image, objects_by_label, traffic_lights):
    draw_objects(image, objects_by_label)
    draw_traffic_lights(image, traffic_lights)

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


def crop_object(image, obj):
    obj_crop = image.crop([obj.bbox[0], obj.bbox[1], obj.bbox[2], obj.bbox[3]])
    return obj_crop


def crop_objects(image, objects):
    return [crop_object(image, obj) for obj in objects]


def image_gen(image_folder_path, camera_info):
    path_to_test_images = pathlib.Path(image_folder_path)
    image_paths = sorted(list(path_to_test_images.glob("*.jpg")))
    for image_path in image_paths:
        image = Image.open(image_path, "r").convert("RGB")
        image = image.resize(camera_info.resolution)
        yield image
