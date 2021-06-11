import logging
import threading
import time
import cv2
from src.pubsub import Observable, Observer


def create_tracker(tracker):
    OPENCV_OBJECT_TRACKERS = {
        "csrt": cv2.TrackerCSRT_create,  # slow but accurate
        "kcf": cv2.TrackerKCF_create,  # fast but easily lose track
        "boosting": cv2.TrackerBoosting_create,  # not good
        "mil": cv2.TrackerMIL_create,  # not good, jumpy
        # "tld": cv2.TrackerTLD_create,
        # "goturn": cv2.TrackerGOTURN_create,
        "medianflow": cv2.TrackerMedianFlow_create,  # fast, works well
        "mosse": cv2.TrackerMOSSE_create,  # does not work at all
    }
    return OPENCV_OBJECT_TRACKERS[tracker]()


class Tracking(Observer):
    def __init__(self, tracker_name, detector_id, camera_capturer_id):
        Observer.__init__(self)
        self._tracker = create_tracker(tracker_name)
        self._detector_id = detector_id
        self._camera_capturer_id = camera_capturer_id
        self._thread = threading.Thread(target=self._track, daemon=True)

    def start(self):
        self._thread.start()

    def _track(self):
        for image, image_time in iter(
            lambda: self.get_msg_from(self._camera_capturer_id), None
        ):
            if not self.empty(self._detector_id):
                (
                    detected_objects,
                    detection_image,
                    detection_image_time,
                ) = self.get_msg_from(self._detector_id)
                logging.debug(
                    "has detected object {} {}".format(
                        detection_image_time, detected_objects
                    )
                )
            logging.debug("got image at time {}".format(image_time))
