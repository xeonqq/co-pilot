from threading import Timer

from src.camera_recorder import StartEvent, StopEvent


class CameraRecorderController(object):
    def __init__(self, camera_recorder):
        self._observers = []
        self._min_recording_time_sec = 60
        self._camera_recorder = camera_recorder
        self._event_queue = []
        self._future_event = None

    def _start_future_stop_event(self):
        if self._future_event is not None and self._future_event.is_alive():
            self._future_event.cancel()
            self._future_event.join()
        self._future_event = Timer(self._min_recording_time_sec, lambda: self._camera_recorder.notify(StopEvent))
        self._future_event.start()

    def notify_on_motion(self, event):
        if not self._camera_recorder.is_recording():
            self._camera_recorder.notify(StartEvent())
        self._start_future_stop_event()
