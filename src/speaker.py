import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import time
import pygame

class Speaker(object):
    def __init__(self):
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound('./sounds/mario/smb_1-up.wav')
        self._last_played_time = time.time()

    def play(self):
        current_time = time.time()
        if current_time - self._last_played_time > 2:
            channel = self.sound.play()
            self._last_played_time = current_time
