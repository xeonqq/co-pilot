#!/bin/bash

source /home/qq/copilot_env/bin/activate
cd /home/qq/co-pilot
python3 -m src.main  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms.tflite  --label models/coco_labels.txt --score_threshold 0.3 --traffic_light_classification_model models/traffic_light.tflite  --traffic_light_label models/traffic_light_labels.txt --blackbox_path=/home/qq --cpu
