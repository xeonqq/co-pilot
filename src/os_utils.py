import os
import pathlib
import subprocess
import time


def is_rtc_available():
    cmd = "timedatectl | grep 'RTC time' | cut -d ':' -f2|sed 's/^ *//g'"
    ps = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    output = ps.communicate()[0].strip()
    return False if output == "n/a".encode("ASCII") else True


def generate_recording_postfix(folder):
    postfix = None
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    if is_rtc_available():
        postfix = time.strftime("%Y%m%d-%H%M%S")
    else:
        counter_file = "{}/counter.txt".format(folder)
        if os.path.isfile(counter_file):
            with open(counter_file, "r+") as f:
                line = f.readline()
                content = line.strip()
                new_count = int(content) + 1
                f.seek(0)
                f.write(str(new_count))
                f.truncate()
        else:
            with open(counter_file, "w+") as f:
                new_count = 0
                f.seek(0)
                f.write(str(new_count))
        postfix = str(new_count)
    return postfix
