import threading
import time
import queue
import logging
from .tape import Tape


class StartEvent(object):
    def execute(self, camera_recorder):
        camera_recorder._start_recording()


class StopEvent(object):
    def execute(self, camera_recorder):
        camera_recorder._stop_recording()


class CameraRecorder(object):
    def __init__(self, camera, led, recording_folder, daemon=True):
        self._folder = recording_folder
        self._folder.mkdir(parents=True, exist_ok=True)
        self._camera = camera
        self._led = led
        self._format = "h264"
        self._tape = Tape(self.fps, self._format)
        self._is_recording = False
        self._event_queue = queue.Queue()
        if daemon:
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()

    @property
    def fps(self):
        return self._camera.framerate

    def is_recording(self):
        return self._is_recording

    def start(self):
        self._event_queue.put(StartEvent())

    def stop(self):
        self._event_queue.put(StopEvent())

    def _start_recording(self):
        if not self._is_recording:
            logging.info("start recording, saving at {}".format(self._folder))
            self._tape.save_at(self._folder)
            self._camera.start_recording(self._tape, format=self._format)
            self._is_recording = True

    def _stop_recording(self):
        if self._is_recording:
            self._camera.stop_recording()
            self._tape.close()
            self._is_recording = False
            logging.info("stop recording")

    def process_event(self):
        if not self._event_queue.empty():
            event = self._event_queue.get()
            event.execute(self)

    def run(self, start_recording=True):
        if start_recording:
            self._start_recording()
        while True:
            if self._is_recording:
                self._camera.wait_recording(1)
                self._led.toggle()
                self.process_event()
            else:
                self._led.off()
                self.process_event()
                time.sleep(0.05)

    def notify(self, event):
        self._event_queue.put(event)
