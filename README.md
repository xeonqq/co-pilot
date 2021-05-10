[![Build Status](https://travis-ci.com/xeonqq/co-pilot.svg?branch=master)](https://travis-ci.com/xeonqq/co-pilot)

<h2 align="center">Co-Pilot</h2>

Traffic light alert and Dashcam all in one.

`Co-Pilot` = Raspberrypi 3/4 + rpi camera + Google Coral TPU.

![](images/traffic_light_detection_seq.gif)
## Watch the demo in car
[![Watch the demo in car](https://i.imgur.com/1PCb91b.png)](https://youtu.be/3rqdppF8GpE)

## Dependencies
```bash on rpi
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
apt-get update
apt-get install -y libedgetpu1-std
apt-get install -y python3-pycoral
apt-get install -y python3-tflite-runtime
python3 -m pip install -r requirements_pi.txt
sudo apt-get install libsdl2-mixer-2.0-0  libsdl2-2.0-0
```
## Run Co-Pilot
```bash
python3 -m src.main  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.3 --traffic_light_classification_model models/traffic_light_edgetpu.tflite  --traffic_light_label models/traffic_light_labels.txt --blackbox_path=./
```

## Test
```bash
# under repo root foler
python3 -m pytest
# or
python3 -m tests.test_detection
python3 -m tests.test_classification
```

## Reprocess with recorded video (On Host PC)

Build and run docker container
```bash
./build.sh
./linux_run.sh
```

In docker container
```bash
cd workspace
python3 -m src.reprocess  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.3 --traffic_light_classification_model models/traffic_light_edgetpu.tflite  --traffic_light_label models/traffic_light_labels.txt --blackbox_path=./ --video recording_20210417-090028.h264.mp4 --fps 5
```

## References
* SSD model is downloaded from https://github.com/google-coral/test_data/blob/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite


