from math import cos, pi


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


class Tracker(object):
    def __init__(self, camera_info):
        self._camera_info = camera_info
        self._traffic_light_tracks = []

    def locate_traffic_light(self, traffic_light):
        traffic_light_vec = self._camera_info.pixel_to_camera_frame(
            traffic_light.center
        )
        traffic_light_vec = traffic_light_vec / np.linalg.norm(traffic_light_vec)

    def update(self, traffic_lights):
        pass

    def _get_driving_relevant_traffic_ligth(self):
        driving_direction = np.array([0, 0, 1])
        for light in self._traffic_light_tracks:
            driving_direction.dot(light.direction)
