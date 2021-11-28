#!/bin/bash
#https://www.thegeekdiary.com/how-to-create-virtual-block-device-loop-device-filesystem-in-linux/
dd if=/dev/zero of=loopbackfile.img bs=10M count=1
du -sh loopbackfile.img
sudo losetup -fP loopbackfile.img
losetup -a
mkfs.ext4 loopbackfile.img
mkdir -p loopfs
sudo mount -o loop /dev/loop0 loopfs
sudo chown $USER:$USER loopfs
