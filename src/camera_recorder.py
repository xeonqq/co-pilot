import threading
import time
import logging
from .tape import Tape


class CameraRecorder(object):
    def __init__(self, camera, led, recording_folder):
        self._folder = recording_folder
        self._folder.mkdir(parents=True, exist_ok=True)
        self._camera = camera
        self._led = led
        self._tape = Tape()
        self._is_recording = False
        # self._button.add_pressed_cb(self._add_toggle_event)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @property
    def fps(self):
        return self._camera.framerate

    @property
    def filename(self):
        return self._filename

    def is_recording(self):
        return self._is_recording

    # def _add_convert_mp4_event(self):
    #    self._events.put(ConvertMP4Event(self))

    # def _process_event(self):
    #    if not self._events.empty():
    #        evt = self._events.get()
    #        evt.execute()

    def _start_recording(self):
        self._filename = "{}/recording_{}.h264".format(
            self._folder, time.strftime("%Y%m%d-%H%M%S")
        )
        logging.info("start recording, saving to {}".format(self._filename))
        self._tape.open(self._filename)
        self._camera.start_recording(self._tape, format="h264")
        self._is_recording = True

    # def on_enter_idle(self):
    #    logging.info("stop recording...")
    #    self._led.off()
    #    self._camera.stop_recording()
    #    self._tape.close()
    #    self._add_convert_mp4_event()

    def _run(self):
        self._start_recording()
        while True:
            self._camera.wait_recording(1)
            self._led.toggle()
