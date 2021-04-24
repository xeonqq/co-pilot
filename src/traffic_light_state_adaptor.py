import time
from .utils import is_green, is_red

class TrafficLightStateAdaptor(object):
    def __init__(self):
        self._prev_state = None
        self._state_to_sound_map = {
            "green": "green",
            "red": "red",
            "yellow": "yellow",
            "red_yellow": "red_yellow",
            "green_left": "green",
            "red_left": "red",
            "green_right": "green",
            "red_right": "red",
            "side": None,
            "none": None,
        }
        self._last_update_time = 0

    def update(self, state):
        sound_track = None
        if not state: # no detected valid traffic light
            if self._time_interval_since_last_update() > 3:
                self._prev_state = None
            return sound_track

        # do not distinguish left right
        traffic_light_state = self._state_to_sound_map.get(state, None)
        if (
            traffic_light_state != self._prev_state
        ) and not self._was_red_yellow_now_green(traffic_light_state):
            sound_track = traffic_light_state

        self._prev_state = traffic_light_state
        self._last_update_time = time.time()

        return sound_track

    def _time_interval_since_last_update(self):
        return time.time() - self._last_update_time

    def _was_red_yellow_now_green(self, traffic_light_state):
        return self._prev_state == "red_yellow" and is_green(traffic_light_state)
