import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
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
                "ready": pygame.mixer.Sound('./sounds/red-alert/visibility-clear.mp3'),
                "traffic": pygame.mixer.Sound('./sounds/mario/smb_1-up.wav'),
                "green":pygame.mixer.Sound('./sounds/wife/green.wav'),
                "red":pygame.mixer.Sound('./sounds/wife/red.wav'),
                "yellow":pygame.mixer.Sound('./sounds/wife/yellow.wav'),
                "red_yellow": pygame.mixer.Sound('./sounds/wife/red-yellow.wav'),
                "green_left": None,
                "red_left": None,
                "side": None,
                "none": None,
                }

    def play(self, key):
        current_time = time.time()
        sound = self._sound_map.get(key, None)
        if sound and current_time - self._last_played_time > 2:
            channel = sound.play()
            self._last_played_time = current_time


