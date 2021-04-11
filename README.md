## Dependencies
```bash
# for sound support
python3 -m pip install -U pygame --user
sudo apt-get install libsdl2-mixer-2.0-0  libsdl2-2.0-0
```
## Run Co-Pilot
```bash
python3 -m src.main  --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.4 --traffic_light_classification_model models/traffic_light_edgetpu.tflite  --traffic_light_label models/traffic_light_labels.txt
```

## Test
```bash
# under repo root foler
python3 -m pytest
# or
python3 -m tests.test_detection
python3 -m tests.test_classification
```

## References
* SSD model is downloaded from https://github.com/google-coral/test_data/blob/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite

## Training data generation from video
python3 -m src.training_data_generator    --ssd_model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.3 --label_extract traffic  --thumbnail_path /mnt/hdd/nn_extracted_traffic_lights --input_paths /mnt/aigo/pi_cam_record/picam2/traffic_light_scene,/mnt/aigo/pi_cam_record/picam2/traffic_light_scene2,/mnt/aigo/pi_cam_record/picam2/traffic_light_scene3
