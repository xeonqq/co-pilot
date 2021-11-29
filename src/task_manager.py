import queue
import argparse
import time
import subprocess
from .button import Button
from .led import Led


class ProcessTask(object):
    def __init__(self, name):
        self._proc = None
        self._name = name

    def stop(self):
        if self._proc:
            print("terminating {}".format(self._name))
            self._proc.terminate()
            self._proc.wait(5)

    def run(self):
        self._proc = subprocess.Popen(self._cmd.split())


class CoPilotTask(ProcessTask):
    def __init__(self, args):
        ProcessTask.__init__(self, "SwitchTaskEvent")
        self._cmd = """python3 -m src.main  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.3 --traffic_light_classification_model models/traffic_light_edgetpu.tflite  --traffic_light_label models/traffic_light_labels.txt --blackbox_path={} --mode=full""".format(
            args.blackbox_path)


class CoPilotTaskMinimal(ProcessTask):
    def __init__(self, args):
        ProcessTask.__init__(self, "SwitchTaskEvent")
        self._cmd = """python3 -m src.main  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.3 --traffic_light_classification_model models/traffic_light_edgetpu.tflite  --traffic_light_label models/traffic_light_labels.txt --blackbox_path={} --mode=minimal""".format(
            args.blackbox_path)


class DashCamTask(ProcessTask):
    def __init__(self, args):
        ProcessTask.__init__(self, "DashCamTask")
        self._cmd = (
            """python3 -m src.dashcam --record_on_motion --blackbox_path={}""".format(args.blackbox_path)
        )


class SwitchTaskEvent(object):
    def __init__(self, args):
        self._tasks = [CoPilotTaskMinimal(args), CoPilotTask(args), DashCamTask(args)]
        self._current_task_index = -1

    def execute(self):
        self._tasks[self._current_task_index].stop()
        self._current_task_index = (self._current_task_index + 1) % len(self._tasks)
        self._tasks[self._current_task_index].run()


class TaskManager(object):
    def __init__(self, args):
        self._button = Button(8)
        self._led = Led(10)
        self._button.add_pressed_cb(self._switch_task)
        self._events = queue.Queue(1)
        self._switch_task_event = SwitchTaskEvent(args)

    def _switch_task(self, pin):
        self._events.put(self._switch_task_event)

    def _process_event(self):
        if not self._events.empty():
            self._led.off()
            evt = self._events.get()
            evt.execute()

    def run(self):
        # first run the default task
        self._switch_task_event.execute()
        while True:
            self._process_event()
            time.sleep(1)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--blackbox_path",
        help="Output path for blackbox (images, detections, video)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    tm = TaskManager(parse_arguments())
    tm.run()
