class ILed(object):
    def on(self):
        pass

    def off(self):
        pass

    def toggle(self):
        pass


class IBlackBox(object):
    def log(self, *args):
        pass

    def stop_and_join(self):
        pass


class ISpeaker(object):
    def play(self, *args):
        pass

    def play_ready(self):
        pass
