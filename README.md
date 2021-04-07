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
