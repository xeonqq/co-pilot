import queue


class PubSub(object):
    def __init__(self):
        self._messages = queue.Queue(1)

    def get(self):
        return self._messages.get()

    def publish(self, msg):
        if self._messages.full():
            self._messages.get()
        self._messages.put(msg)
