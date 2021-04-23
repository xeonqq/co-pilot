import os


os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import time
import pygame


class TrafficLightMachine(object):
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
        self._red_states = {"red", "red_left", "red_right"}
        self._green_states = {"green", "green_left", "green_right"}

    def update(self, state):
        # do not distinguish left right
        traffic_light_state = self._state_to_sound_map.get(state, None)
        sound_track = None
        if (
            traffic_light_state != self._prev_state
        ) and not self._was_red_yellow_now_green(traffic_light_state):
            sound_track = traffic_light_state

        self._prev_state = traffic_light_state

        return sound_track

    def _was_red_yellow_now_green(self, traffic_light_state):
        return self._prev_state == "red_yellow" and self.is_green(traffic_light_state)

    def is_red(self, state):
        return state in self._red_states

    def is_green(self, state):
        return state in self._green_states


class SlientSound(object):
    def play(self):
        pass


class Speaker(object):
    def __init__(self):
        pygame.mixer.init()
        self._last_played_time = 0
        self._sound_tracks = {
            "visibility_clear": pygame.mixer.Sound(
                "./sounds/red-alert/visibility-clear.wav"
            ),
            "1-up": pygame.mixer.Sound("./sounds/mario/smb_1-up.wav"),
            "green": pygame.mixer.Sound("./sounds/wife/green.wav"),
            "red": pygame.mixer.Sound("./sounds/wife/red.wav"),
            "yellow": pygame.mixer.Sound("./sounds/wife/yellow.wav"),
            "red_yellow": pygame.mixer.Sound("./sounds/wife/red-yellow.wav"),
        }
        self._prev_sound_key = None

    def play(self, key):

        current_time = time.time()

        if (key != self._prev_sound_key) or (current_time - self._last_played_time > 1):
            sound = self._sound_tracks.get(key, None)
            if not sound:
                return
            channel = sound.play()
            self._prev_sound_key = key
            self._last_played_time = current_time
