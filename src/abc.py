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