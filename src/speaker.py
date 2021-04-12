import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import time
import pygame


class SlientSound(object):
    def play(self):
        pass


class Speaker(object):
    def __init__(self):
        pygame.mixer.init()
        self._last_played_time = 0
        self._sound_tracks = {
                "visibility_clear": pygame.mixer.Sound("./sounds/red-alert/visibility-clear.mp3"),
                "1-up": pygame.mixer.Sound("./sounds/mario/smb_1-up.wav"),
                "green": pygame.mixer.Sound("./sounds/wife/green.wav"),
                "red": pygame.mixer.Sound("./sounds/wife/red.wav"),
                "yellow": pygame.mixer.Sound("./sounds/wife/yellow.wav"),
                "red_yellow": pygame.mixer.Sound("./sounds/wife/red-yellow.wav"),
            }
        self._sound_map = {
            "ready": "visibility_clear",
            "traffic": "1-up",
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
        self._prev_sound_key = None

    def play(self, key):
        if key in ["side","none"]:
            return

        current_time = time.time()
        if (key != self._prev_sound_key) or (current_time - self._last_played_time> 8):
            sound_track_name = self._sound_map.get(key, None)
            sound = self._sound_tracks.get(sound_track_name, None)
            if not sound:
                return
            channel = sound.play()
            self._prev_sound_key = key
            self._last_played_time = current_time
