import threading
import io
import queue


class Tape(object):
    MAX_QUEUE_SIZE = 10
    MAX_BUFFER_SIZE = (
        1 * 1024 * 1024
    )  # memory buffer size, before put into the queue for disk writing

    def __init__(self):
        self._tape_queue = queue.Queue(Tape.MAX_QUEUE_SIZE)
        self._buffer_size = 0
        self._buffer = io.BytesIO()

    def _record(self):
        with open(self._filename, "wb") as f:
            for data in iter(self._tape_queue.get, None):
                f.write(data)

    def open(self, filename):
        self._filename = filename
        self._thread = threading.Thread(target=self._record)
        self._thread.start()

    def _write_buffer_to_queue(self):
        self._buffer.truncate()
        self._tape_queue.put(self._buffer.getvalue())
        self._buffer.seek(0)
        self._buffer_size = 0

    def write(self, frame):
        self._buffer.write(frame)
        self._buffer_size += len(frame)

        if self._buffer_size > Tape.MAX_BUFFER_SIZE:
            self._write_buffer_to_queue()

    def flush(self):
        if self._buffer_size > 0:
            self._write_buffer_to_queue()

    def close(self):
        self.flush()
        self._tape_queue.put(None)
        self._thread.join()
