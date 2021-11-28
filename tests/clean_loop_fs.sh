#!/bin/bash
if [ $EUID != 0 ]; then
    sudo "$0" "$@"
    exit $?
fi
umount loopfs
rm -rf loopfs
losetup -d /dev/loop0
rm loopbackfile.img

