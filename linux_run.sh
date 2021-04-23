#!/bin/bash
xhost +SI:localuser:root
docker run --rm -v /tmp/.X11-unix:/tmp/.X11-unix \
-e DISPLAY=$DISPLAY   \
-it -p 5005:5005 -v "$(pwd)":/workspace  -v /media/qq/5256C31056C2F3AF5/pi_cam_record/picam2/:/mnt/hdd --privileged -v /dev/bus/usb:/dev/bus/usb -p 8888:8888 -p 6006:6006 co-pilot:latest /bin/bash
