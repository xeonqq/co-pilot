import os


os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import time
import pygame


class SlientSound(object):
    def play(self):
        pass


def get_en_sound_tracks():
    return {
        "visibility_clear": pygame.mixer.Sound(
            "./sounds/red-alert/visibility-clear.wav"
        ),
        "dashcam": pygame.mixer.Sound(
            "./sounds/red-alert/standing-by.wav"
        ),
        "dead": pygame.mixer.Sound("./sounds/red-alert/im-gone.wav"),
        "1-up": pygame.mixer.Sound("./sounds/mario/smb_1-up.wav"),
        "green": pygame.mixer.Sound("./sounds/en/green.wav"),
        "red": pygame.mixer.Sound("./sounds/en/red.wav"),
        "yellow": pygame.mixer.Sound("./sounds/en/yellow.wav"),
        "red_yellow": pygame.mixer.Sound("./sounds/en/red-yellow.wav"),
    }


def get_cn_sound_tracks():
    return {
        "visibility_clear": pygame.mixer.Sound(
            "./sounds/red-alert/visibility-clear.wav"
        ),
        "speed_to_full": pygame.mixer.Sound(
            "./sounds/red-alert/speed-to-full.wav"
        ),
        "dashcam": pygame.mixer.Sound(
            "./sounds/red-alert/standing-by.wav"
        ),
        "dead": pygame.mixer.Sound("./sounds/red-alert/im-gone.wav"),
        "1-up": pygame.mixer.Sound("./sounds/mario/smb_1-up.wav"),
        "green": pygame.mixer.Sound("./sounds/cn/green.wav"),
        "red": pygame.mixer.Sound("./sounds/cn/red.wav"),
        "yellow": pygame.mixer.Sound("./sounds/cn/yellow.wav"),
        "red_yellow": pygame.mixer.Sound("./sounds/cn/red-yellow.wav"),
    }


class Speaker(object):
    def __init__(self, lang="en"):
        pygame.mixer.init()
        lang_sound_track_map = {"cn": get_cn_sound_tracks, "en": get_en_sound_tracks}
        self._sound_tracks = lang_sound_track_map[lang]()
        self._last_played_time = 0
        self._prev_sound_key = None

    def play_ready(self, mode):
        if mode == 'full':
            self.play_sound('speed_to_full')
        else:
            self.play_sound("visibility_clear")

    def play_sound(self, key, is_blocking=False):
        sound = self._sound_tracks.get(key, None)
        if not sound:
            return
        channel = sound.play()

        if not is_blocking:
            return
        while channel.get_busy():
            pass

    def play(self, key):
        current_time = time.time()

        if (key != self._prev_sound_key) or (current_time - self._last_played_time > 1):
            sound = self._sound_tracks.get(key, None)
            if not sound:
                return
            channel = sound.play()
            self._prev_sound_key = key
            self._last_played_time = current_time
