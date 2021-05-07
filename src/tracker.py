from math import cos, pi, atan
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter
import numpy as np

from .traffic_light import TrafficLight
from .utils import intersection_of_union, magnify_bbox

PlausibleTrafficLightTransitionMap = {
    "green": {"yellow", "red", "red_left", "red_right", "green_left", "green_right"},
    "green_left": {"yellow", "red", "red_left", "red_right", "green"},
    "green_right": {"yellow", "red", "red_left", "red_right", "green"},
    "red": {"red_yellow", "green", "green_left", "green_right"},
    "red_left": {"red_yellow", "green", "green_left", "green_right"},
    "red_right": {"red_yellow", "green", "green_left", "green_right"},
    "yellow": {"red", "red_left", "red_right"},
    "red_yellow": {"green", "green_left", "green_right"},
}

LaneWidth = 3


class TrafficLightTrack(object):
    TrackID = 0

    def __init__(self, camera_info, traffic_light):
        TrafficLightTrack.TrackID += 1
        self._track_id = TrafficLightTrack.TrackID

        self._traffic_light = traffic_light
        self._bbox = traffic_light.obj.bbox
        self._camera_info = camera_info
        # self._update_position()
        self._energy_upper_bound = 3
        self._energy = self._energy_upper_bound
        self._vote = 0
        self._cls = traffic_light.cls
        self._prev_traffic_light = traffic_light
        self._setup_kf(dt=0.5)

    def _setup_kf(self, dt):
        self._kf = KalmanFilter(dim_x=6, dim_z=2)
        self._kf.x = np.array([*self._traffic_light.center, 0, 0, 0, 0])
        self._kf.F = np.array(
            [
                [1, 0, dt, 0, 0.5 * dt ** 2, 0],
                [0, 1, 0, dt, 0, 0.5 * dt ** 2],
                [0, 0, 1, 0, dt, 0],
                [0, 0, 0, 1, 0, dt],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ]
        )
        self._kf.H = np.zeros((2, 6))
        self._kf.H[0, 0] = 1
        self._kf.H[1, 1] = 1
        self._kf.P *= 100
        self._kf.R *= 1

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
    def id(self):
        return self._track_id

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

    def _update_bbox(self, center):
        half_width = self._traffic_light.width / 2.0
        half_height = self._traffic_light.height / 2.0
        xmin = center[0] - half_width
        xmax = center[0] + half_width
        ymin = center[1] - half_height
        ymax = center[1] + half_height
        self._bbox = [xmin, ymin, xmax, ymax]

    def predict_bbox(self):
        # print("Before pred ", self._track_id, self._kf.x, self._traffic_light.center)
        self._kf.predict()
        # print("Predicted ", self._track_id, self._kf.x)
        self._update_bbox(self._kf.x[:2])
        return self._bbox

    def update(self, traffic_light):
        self._kf.update(traffic_light.center)
        # print("After update ", self._track_id, self._kf.x, traffic_light.center)
        self._update_bbox(self._kf.x[:2])

        self._update_state(traffic_light)
        self._feed()

    def _update_state(self, traffic_light):
        if (
            traffic_light.cls in PlausibleTrafficLightTransitionMap[self._cls]
        ):  # update when it is a plausible transition
            self._cls = traffic_light.cls
        elif (
            traffic_light.cls == self._prev_traffic_light.cls
        ):  # update when two consequtive same classification
            self._cls = traffic_light.cls
        # print(traffic_light.cls, self._cls)

        self._prev_traffic_light = self._traffic_light
        self._traffic_light = traffic_light

    @property
    def score(self):
        return self._traffic_light.score

    @property
    def obj(self):
        return self._traffic_light.obj

    @property
    def bbox(self):
        return self._bbox

    @property
    def center(self):
        return np.asarray(
            [(self._bbox[0] + self._bbox[2]) / 2, (self._bbox[1] + self._bbox[3]) / 2]
        )

    @property
    def width(self):
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self):
        return self.bbox[3] - self.bbox[1]

    @property
    def area(self):
        return self.width * self.height

    @property
    def cls(self):
        return self._cls

    @property
    def alive(self):
        return self._energy > 0

    def decay(self):
        self._energy -= 1

    def _feed(self):
        # TODO: should be adaptive with frame rate
        self._energy = self._energy_upper_bound

    def add_vote(self):
        self._vote += 1
        if (
            self._vote % 10 == 0
        ):  # delay the prune to prevent detection of other tracks during crossing
            self._energy_upper_bound = min(self._energy_upper_bound + 1, 10)

    def get_vote(self):
        return self._vote

    def __repr__(self):
        return "<TrafficLightTrack {}: {} energy {} vote {}>".format(
            self.id, self.cls, self._energy, self._vote
        )


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
        scores.append(area / (2 * d))
    if scores:
        selected_inx = np.argsort(scores)
        return traffic_lights[selected_inx[-1]]
    else:
        return None


class Tracker(object):
    def __init__(self, camera_info):
        self._camera_info = camera_info
        self._traffic_light_tracks = []
        self._driving_relevant_track = None

    def _match(self, traffic_lights):
        rows = len(traffic_lights)  # new detections
        cols = len(self._traffic_light_tracks)  # existing tracks

        weight = np.zeros((rows, cols))

        bboxes = np.array(
            [track.predict_bbox() for track in self._traffic_light_tracks]
        )
        for i, traffic_light in enumerate(traffic_lights):
            ious = intersection_of_union(magnify_bbox(traffic_light, 3), bboxes)
            weight[i, :] = ious

        row_ind, col_ind = linear_sum_assignment(weight, maximize=True)
        matched_detected_traffic_lights_ind = []
        matched_traffic_light_tracks_ind = []
        for r, c in zip(row_ind, col_ind):
            if weight[r, c] > 0:
                matched_detected_traffic_lights_ind.append(r)
                matched_traffic_light_tracks_ind.append(c)
        # print(
        #     "cost {}, match: {}:{}".format(
        #         weight,
        #         matched_detected_traffic_lights_ind,
        #         matched_traffic_light_tracks_ind,
        #     )
        # )
        return matched_detected_traffic_lights_ind, matched_traffic_light_tracks_ind

    def track(self, detected_traffic_lights):
        # print("----------------------")
        traffic_lights = list(filter(is_valid_traffic_light, detected_traffic_lights))
        # print("detected: ", traffic_lights)
        # print("existing tracks: ", self._traffic_light_tracks)
        if not self._traffic_light_tracks:
            self._traffic_light_tracks = [
                TrafficLightTrack(self._camera_info, traffic_light)
                for traffic_light in traffic_lights
            ]
            # print("init: ", self._traffic_light_tracks)
        else:
            (
                matched_detected_traffic_lights_ind,
                matched_traffic_light_tracks_ind,
            ) = self._match(traffic_lights)

            # update matched existing tracks
            for detected_traffic_light_ind, traffic_light_track_ind in zip(
                matched_detected_traffic_lights_ind, matched_traffic_light_tracks_ind
            ):
                self._traffic_light_tracks[traffic_light_track_ind].update(
                    traffic_lights[detected_traffic_light_ind]
                )

            # add new tracks
            n_detected_traffic_lights = len(traffic_lights)
            newly_detected_inds = set(range(n_detected_traffic_lights)) - set(
                matched_detected_traffic_lights_ind
            )
            # print("new:", newly_detected_inds)
            for ind in newly_detected_inds:
                self._traffic_light_tracks.append(
                    TrafficLightTrack(self._camera_info, traffic_lights[ind])
                )

        self._prune_tracks()
        self._vote_for_driving_relevant()
        self._driving_relevant_track = self._select_driving_relevant_track()
        # print("end tracks: ", self._traffic_light_tracks)
        return self._traffic_light_tracks

    def _prune_tracks(self):
        for tl_track in self._traffic_light_tracks:
            tl_track.decay()
        self._traffic_light_tracks[:] = [
            track for track in self._traffic_light_tracks if track.alive
        ]

    def _vote_for_driving_relevant(self):
        scores = []
        view_center = np.array(
            [self._camera_info.pixel_center[0], self._camera_info.pixel_center[1] * 0.6]
        )
        for track in self._traffic_light_tracks:
            d = np.linalg.norm(track.center - view_center)
            scores.append(track.area / (2 * d))
        if scores:
            selected_inx = np.argmax(scores)
            self._traffic_light_tracks[selected_inx].add_vote()

    @property
    def tracks(self):
        return self._traffic_light_tracks

    def _select_driving_relevant_track(self):
        if self._traffic_light_tracks:
            f = lambda i: self._traffic_light_tracks[i].get_vote()
            ind = max(range(len(self._traffic_light_tracks)), key=f)
            return self._traffic_light_tracks[ind]
        return None

    def get_driving_relevant_track(self):
        return self._driving_relevant_track
