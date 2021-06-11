import queue
from collections import defaultdict


class PubSub(object):
    def __init__(self):
        self._messages = queue.Queue(1)

    def get(self):
        return self._messages.get()

    def publish(self, msg):
        if self._messages.full():
            self._messages.get()
        self._messages.put(msg)


class Model(object):
    def __init__(self):
        self._messages = queue.Queue(1)

    def get(self):
        return self._messages.get()

    def put(self, msg):
        if self._messages.full():
            self._messages.get()
        self._messages.put(msg)

    def empty(self):
        return self._messages.empty()


class Observer(object):
    def __init__(self):
        self._models = {}

    def notify(self, observable_id, msg):
        self._models[observable_id].put(msg)

    def add_model(self, observable_id):
        self._models[observable_id] = Model()

    def get_msg_from(self, observable_id):
        return self._models[observable_id].get()

    def empty(self, observable_id):
        return self._models[observable_id].empty()

    def get(self):
        return next(iter(self._models.items()))[1].get()


class Observable(object):
    def __init__(self):
        self._observers = []

    def add_observer(self, obs):
        self._observers.append(obs)
        obs.add_model(self.get_id())

    def publish(self, msg):
        for obs in self._observers:
            obs.notify(self.get_id(), msg)

    def get_id(self):
        raise NotImplementedError
