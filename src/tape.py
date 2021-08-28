import subprocess
import time
import threading
import io
import queue
import shutil


class Tape(object):
    MAX_QUEUE_SIZE = 10
    MAX_BUFFER_SIZE = (
        1 * 1024 * 1024
    )  # memory buffer size, before put into the queue for disk writing

    def __init__(self, fps, format):
        self._tape_queue = queue.Queue(Tape.MAX_QUEUE_SIZE)
        self._buffer_size = 0
        self._buffer = io.BytesIO()
        self._fps = fps
        self._format = format

    def _record(self):
        for data in iter(self._tape_queue.get, None):
            data.seek(0)
            shutil.copyfileobj(data, self._proc.stdin)
            data.close()

    def save_at(self, folder):
        self._filepath = "{}/recording_{}_%03d.mp4".format(
            folder, time.strftime("%Y%m%d-%H%M%S")
        )
        self._ffmpeg_cmd = """ffmpeg -v 16 -framerate {0} -f {1}
                                    -i pipe:0 -codec copy 
                                    -movflags faststart
                                    -segment_time 00:05:00 -f segment -reset_timestamps 1
                                    -y {2}""".format(
            self._fps,
            self._format,
            self._filepath)
        self._proc = subprocess.Popen(self._ffmpeg_cmd.split(),
                                      stdin=subprocess.PIPE)

        self._thread = threading.Thread(target=self._record)
        self._thread.start()

    def _write_buffer_to_queue(self):
        self._buffer.truncate()
        self._tape_queue.put(self._buffer)
        self._buffer = io.BytesIO()
        self._buffer_size = 0

    def write(self, frame):
        self._buffer.write(frame)
        self._buffer_size += len(frame)

        if self._buffer_size > Tape.MAX_BUFFER_SIZE:
            self._write_buffer_to_queue()

    def _flush(self):
        if self._buffer_size > 0:
            self._write_buffer_to_queue()

    def close(self):
        self._flush()
        self._tape_queue.put(None)
        self._thread.join()

        self._proc.stdin.flush()
        self._proc.stdin.close()
        self._proc_wait()
