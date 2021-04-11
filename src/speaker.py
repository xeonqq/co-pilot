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
        self._sound_map = {
            "ready": pygame.mixer.Sound("./sounds/red-alert/visibility-clear.mp3"),
            "traffic": pygame.mixer.Sound("./sounds/mario/smb_1-up.wav"),
            "green": pygame.mixer.Sound("./sounds/wife/green.wav"),
            "red": pygame.mixer.Sound("./sounds/wife/red.wav"),
            "yellow": pygame.mixer.Sound("./sounds/wife/yellow.wav"),
            "red_yellow": pygame.mixer.Sound("./sounds/wife/red-yellow.wav"),
            "green_left": pygame.mixer.Sound("./sounds/wife/green.wav"),
            "red_left": pygame.mixer.Sound("./sounds/wife/red.wav"),
            "side": None,
            "none": None,
        }
        self._prev_sound_key = None

    def play(self, key):
        if key in ["side","none"]:
            return

        current_time = time.time()
        if (key != self._prev_sound_key) or (current_time - self._last_played_time> 8):
            sound = self._sound_map.get(key, None)
            channel = sound.play()
            self._prev_sound_key = key
            self._last_played_time = current_time
