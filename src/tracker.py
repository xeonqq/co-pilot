from math import cos, pi, atan
from scipy.optimize import linear_sum_assignment
import numpy as np
from .traffic_light import TrafficLight

PlausibleTrafficLightTransitionMap = {
    "green": {"yellow","red", "red_left","red_right"},
    "green_left": {"yellow","red", "red_left","red_right"},
    "green_right": {"yellow","red", "red_left","red_right"},
    "red": {"red_yellow", "green","green_left", "green_right"},
    "red_left": {"red_yellow", "green","green_left", "green_right"},
    "red_right": {"red_yellow", "green","green_left", "green_right"},
    "yellow": {"red", "red_left", "red_right"},
    "red_yellow": {"green","green_left", "green_right"}
}

LaneWidth = 3


class TrafficLightTrack(object):
    TrackID=0
    def __init__(self, camera_info, traffic_light):
        TrafficLightTrack.TrackID += 1
        self._track_id = TrafficLightTrack.TrackID

        self._traffic_light = traffic_light
        self._camera_info = camera_info
        #self._update_position()
        self._feed()
        self._cls= traffic_light.cls
        self._prev_traffic_light = traffic_light


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

    def update(self, traffic_light):
        self._feed()
        self._update_state(traffic_light)

    def _update_state(self, traffic_light):
        if traffic_light.cls in PlausibleTrafficLightTransitionMap[self._cls]: # update when it is a plausible transition
            self._cls = self._traffic_light.cls
        elif traffic_light.cls == self._prev_traffic_light.cls: # update when two consequtive same classification
            self._cls = traffic_light.cls

        self._prev_traffic_light = self._traffic_light
        self._traffic_light = traffic_light

    @property
    def score(self):
        return self._traffic_light.score

    @property
    def obj(self):
        return self._traffic_light.obj

    @property
    def center(self):
        return self._traffic_light.center

    @property
    def cls(self):
        return self._cls

    @property
    def alive(self):
        return self._energy > 0

    def decay(self):
        self._energy -= 1

    def _feed(self):
        #TODO: should be adaptive with frame rate
        self._energy = 3


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

    def _match(self, traffic_lights):
        rows = len(traffic_lights)  # new detections
        cols = len(self._traffic_light_tracks)  # existing tracks

        cost = np.zeros((rows, cols))
        for i, traffic_light in enumerate(traffic_lights):
            for j, traffic_light_track in enumerate(self._traffic_light_tracks):
                cost[i, j] = traffic_light.center_pixel_distance(
                    traffic_light_track.center
                )
        print("cost, ", cost)
        row_ind, col_ind = linear_sum_assignment(cost)
        return row_ind, col_ind

    def track(self, detected_traffic_lights):

        traffic_lights = list(filter(is_valid_traffic_light, detected_traffic_lights))
        if not self._traffic_light_tracks:
            self._traffic_light_tracks = [TrafficLightTrack(self._camera_info, traffic_light) for traffic_light in traffic_lights]
            print("init: ", self._traffic_light_tracks)
        else:
            detected_traffic_lights_ind, traffic_light_tracks_ind = self._match(traffic_lights)

            print("track: ", detected_traffic_lights_ind, traffic_light_tracks_ind)
            # update matched existing tracks
            for detected_traffic_light_ind, traffic_light_track_ind in zip(detected_traffic_lights_ind, traffic_light_tracks_ind):
                self._traffic_light_tracks[traffic_light_track_ind].update(traffic_lights[detected_traffic_light_ind])

            # add new tracks
            n_detected_traffic_lights = len(traffic_lights)
            newly_detected_inds = set(range(n_detected_traffic_lights)) - set(traffic_light_tracks_ind)
            print ("new:", newly_detected_inds)
            for ind in newly_detected_inds:
                self._traffic_light_tracks.append(TrafficLightTrack(self._camera_info,traffic_lights[ind]))

        self._prune_tracks()
        return self._traffic_light_tracks

    def _prune_tracks(self):
        for tl_track in self._traffic_light_tracks:
            tl_track.decay()
        self._traffic_light_tracks[:] = [track for track in self._traffic_light_tracks if track.alive]

