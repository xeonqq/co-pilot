from math import cos, pi
#from scipy.optimize import linear_sum_assignment
import numpy as np


class TrafficLightTrack(object):
    LaneWidth = 3

    def __init__(self, camera_info, traffic_light):
        self._traffic_light = traffic_light
        self._camera_info = camera_info
        self._update_position()

    def _update_position(self):
        # position for now is just a unit vector pointing from camera to center of traffic light

        traffic_light_camera_frame = self._camera_info.pixel_to_camera_frame(
            self._traffic_light.center
        )

        self._direction_vec = traffic_light_camera_frame / np.linalg.norm(
            traffic_light_camera_frame
        )

        h_w_pixel_ratio = self._traffic_light.height / self._traffic_light.width
        if h_w_pixel_ratio > TrafficLight.H_W_RATIO:  # pixel height more trustworthy
            scale = TrafficLight.WORLD_HEIGHT / self._traffic_light.height
        else:
            scale = TrafficLight.WORLD_WIDTH / self._traffic_light.width

        self._pos_approx_cam_frame = traffic_light_camera_frame * scale

    @property
    def position_approx(self):
        return self._pos_approx_cam_frame

    @property
    def direction(self):
        return self._direction_vec

    def match(self, traffic_light):
        position_error = self._pos_approx_cam_frame - self.position_approx
        # sqr_position_error = position_error.dot(position_error)
        # if sqr_position_error > 4:
        #    return False

        if abs(position_error[2]) > 1:
            # check height
            return False

        proj = traffic_light.direction.dot(self._direction_vec)

        # the further the light is, the lower the angle tolerance

        angle_tolerance = atan(LaneWidth / self._pos_approx_cam_frame[2])

        angle_proj_tolerance = cos(pi / 180 * angle_tolerance)

        if proj < angle_proj_tolerance:
            # diff in angle larger than angle_tolerance
            return False

        return True

    def update(self, traffic_light):
        self._traffic_light = traffic_light
        self._update_position()


def is_valid_traffic_light(traffic_light):
    valid_states = {
        "green",
        "red",
        "yellow",
        "red_yellow",
        "green_left",
        "red_left",
        "green_right",
        "red_right",
    }
    if traffic_light.cls in valid_states:
        return True
    else:
        return False


def selected_driving_relevant(detected_traffic_lights, camera_info):
    traffic_lights = list(filter(is_valid_traffic_light, detected_traffic_lights))

    scores = []
    for traffic_light in traffic_lights:
        d = traffic_light.center_pixel_distance(camera_info.pixel_center)
        area = traffic_light.area
        scores.append(area/(2*d))
    if scores:
        selected_inx = np.argsort(scores)
        return traffic_lights[selected_inx[-1]]
    else:
        return None


class Tracker(object):
    def __init__(self, camera_info):
        self._camera_info = camera_info
        self._traffic_light_tracks = []
        self._relevant_ind = None

    def _match(self, detected_traffic_lights):
        traffic_lights = list(filter(is_valid_traffic_light, detected_traffic_lights))

        if not detected_traffic_lights:  # traffic_light detected, clear track
            self._traffic_light_tracks = []
            return

        if not self._traffic_light_tracks:
            self._traffic_light_tracks = traffic_lights
            return

        rows = len(traffic_lights)  # new detections
        cols = len(self._traffic_light_tracks)  # existing tracks

        cost = np.zeros((rows, cols))
        for i, traffic_light in enumerate(traffic_lights):
            for j, traffic_light_track in enumerate(self._traffic_light_tracks):
                cost[i, j] = traffic_light.center_pixel_distance(
                    traffic_light_track.center
                )
        row_ind, col_ind = linear_sum_assignment(cost)

        for row, col in zip(row_ind, col_ind):
            self._traffic_light_tracks[col].update(traffic_lights[row])

        if rows < cols:
            # remove unmatched track
            unmatched_inds = set(range(cols)) - set(col_ind)
            for ind in unmatched_inds:
                del self._traffic_light_tracks[ind]
        else:
            newly_detected_inds = set(range(rows)) - set(row_ind)
            for ind in newly_detected_inds:
                self._traffic_light_tracks.append(traffic_light[ind])

    def track(self, detected_traffic_lights):
        self._match(detected_traffic_lights)

        self._update_driving_relevant_traffic_light_idx()

        print(self._relevant_ind)

    def _update_driving_relevant_traffic_light_idx(self):
        current_distance = np.inf
        for i, traffic_light in enumerate(self._traffic_light_tracks):
            distance_to_center = traffic_light.center_pixel_distance(
                self._camera_info.pixel_center
            )
            if distance_to_center < current_distance:
                if self._relevant_ind != i:
                    # new relevant traffic_light updated
                    self._relevant_ind = i
                current_distance = distance_to_center

        for i in range(len(self._traffic_light_tracks)):
            self._traffic_light_tracks[i].set_driving_relevance(i == self._relevant_ind)
