import threading
import logging
from .tape import Tape


class CameraRecorder(object):
    def __init__(self, camera, led, recording_folder, daemon=True):
        self._folder = recording_folder
        self._folder.mkdir(parents=True, exist_ok=True)
        self._camera = camera
        self._led = led
        self._format = "h264"
        self._tape = Tape(self.fps, self._format)
        self._is_recording = False
        if daemon:
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()

    @property
    def fps(self):
        return self._camera.framerate

    def is_recording(self):
        return self._is_recording

    def _start_recording(self):
        logging.info("start recording, saving at {}".format(self._folder))
        self._tape.save_at(self._folder)
        self._camera.start_recording(self._tape, format=self._format)
        self._is_recording = True

    def run(self):
        self._start_recording()
        while True:
            self._camera.wait_recording(1)
            self._led.toggle()
