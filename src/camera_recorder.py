import threading
import time
import queue
import logging
# from .tape import Tape
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

class StartEvent(object):
    def execute(self, camera_recorder):
        camera_recorder._start_recording()


class StopEvent(object):
    def execute(self, camera_recorder):
        camera_recorder._stop_recording()

class CameraRecorder(object):
    def __init__(self, camera, fps, led, recording_folder, daemon=True):
        self._folder = recording_folder
        self._folder.mkdir(parents=True, exist_ok=True)
        self._camera = camera
        self._led = led
        self._fps = fps
        # self._tape = Tape(self.fps, self._format)
        self._is_recording = False
        self._event_queue = queue.Queue()
        self._encoder = H264Encoder(10000000)
        filepath = "{}/recording_{}_%03d.mp4".format(
            self._folder, time.strftime("%Y%m%d-%H%M%S")
        )
        options = "-movflags faststart -segment_time 00:01:00 -f segment -reset_timestamps 1 -y "
        self._tape = FfmpegOutput(options + filepath)
        if daemon:
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()

    @property
    def fps(self):
        return self._fps
        #metadata = self._camera.capture_metadata()
        #framerate = 1000000 / metadata["FrameDuration"]
        #return framerate

    def is_recording(self):
        return self._is_recording

    def start(self):
        self._event_queue.put(StartEvent())

    def stop(self):
        self._event_queue.put(StopEvent())

    def _start_recording(self):
        if not self._is_recording:
            logging.info("start recording, saving at {}".format(self._folder))
            # self._tape.save_at(self._folder)
            self._camera.start_recording(self._encoder, self._tape)
            self._is_recording = True

    def _stop_recording(self):
        if self._is_recording:
            self._camera.stop_recording()
            #self._tape.close()
            self._is_recording = False
            logging.info("stop recording")

    def process_event(self):
        if not self._event_queue.empty():
            event = self._event_queue.get()
            event.execute(self)

    def run(self, start_recording=True):
        if start_recording:
            logging.info("start camera recording")
            self._start_recording()
        while True:
            if self._is_recording:
                # self._camera.wait_recording(1)
                # self._led.toggle()
                self.process_event()
            # else:
                # self._led.off()
                # self.process_event()
                time.sleep(0.5)

    def notify(self, event):
        self._event_queue.put(event)
