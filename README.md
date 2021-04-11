## Dependencies
```bash
# for sound support
python3 -m pip install -U pygame --user
sudo apt-get install libsdl2-mixer-2.0-0  libsdl2-2.0-0
```
## Run Detection
```bash
python3 -m src.main  --model models/ssd_mobilenet_v2_coco_quant_no_nms_edgetpu.tflite  --label models/coco_labels.txt --score_threshold 0.4
```

## Test
```bash
# under repo root foler
python3 -m pytest
# or
python3 -m tests.test_detection
```

## References
* SSD model is downloaded from https://github.com/google-coral/test_data/blob/master/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite
