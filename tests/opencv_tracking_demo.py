import argparse
import time
import cv2

def create_tracker(tracker):
    OPENCV_OBJECT_TRACKERS = {
            "csrt": cv2.TrackerCSRT_create, # slow but accurate
            "kcf": cv2.TrackerKCF_create, # fast but easily lose track
            "boosting": cv2.legacy.TrackerBoosting_create, # not good
            "mil": cv2.TrackerMIL_create, # not good, jumpy
            # "tld": cv2.TrackerTLD_create,
            # "goturn": cv2.TrackerGOTURN_create,
            "medianflow": cv2.legacy.TrackerMedianFlow_create, # fast, works well
            "mosse": cv2.legacy.TrackerMOSSE_create # does not work at all
            }
    return OPENCV_OBJECT_TRACKERS[tracker]()


def tracking_demo(tracker_name, video_file):
	video = cv2.VideoCapture(video_file)
	ok, frame = video.read()
	tracker = create_tracker(tracker_name)
	bbox = cv2.selectROI(frame)
	ok = tracker.init(frame, bbox)
	while True:
		# Read a new frame
		ok, frame = video.read()
		if not ok:
			break

		# Start timer
		timer = cv2.getTickCount()

		# Update tracker
		ok, bbox = tracker.update(frame)

		# Calculate Frames per second (FPS)
		fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);

		# Draw bounding box
		if ok:
			# Tracking success
			p1 = (int(bbox[0]), int(bbox[1]))
			p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
			cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
		else:
			# Tracking failure
			cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

			tracker = create_tracker(tracker_name)
			bbox = cv2.selectROI(frame)
			tracker.init(frame, bbox)

		# Display tracker type on frame
		cv2.putText(frame, tracker_name + " Tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2);

		# Display FPS on frame
		cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2);

		# Display result
		cv2.imshow("Tracking", frame)

		# Exit if ESC pressed
		k = cv2.waitKey(4) & 0xff
		if k == 27: break

def main():
    print(cv2.__version__)
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", type=str, required=True,
            help="path to input video file")
    ap.add_argument("-t", "--tracker", type=str, default="kcf",
            help="OpenCV object tracker type")
    args = ap.parse_args()
    print("using tacker: ",args.tracker)
    tracking_demo(args.tracker, args.video)


main()
