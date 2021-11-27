import time
from transitions import Machine, State


class TrafficLightDetectionToSound(object):
    states = [
        State(name='none', on_exit=['reset_sound']),
        State(name='red', on_enter=['update_time'], on_exit=['reset_sound']),
        State(name='green', on_enter=['update_time'], on_exit=['reset_sound']),
        State(name='yellow', on_enter=['update_time'], on_exit=['reset_sound']),
        State(name='red_yellow', on_enter=['update_time'], on_exit=['reset_sound']),
        State(name='implausible', on_enter=['update_time'], on_exit=['reset_sound']),
    ]

    def __init__(self):
        self._sound_track = None
        self._last_update_time = time.time()

        self._machine = Machine(model=self, states=TrafficLightDetectionToSound.states, initial='none')
        self._machine.add_transition('on_green', 'green', '=')
        self._machine.add_transition('on_red', 'red', '=')
        self._machine.add_transition('on_red_yellow', 'red_yellow', '=')
        self._machine.add_transition('on_yellow', 'yellow', '=')

        self._machine.add_transition('on_green', 'implausible', 'green')
        self._machine.add_transition('on_red', 'implausible', 'red')
        self._machine.add_transition('on_red_yellow', 'implausible', 'red_yellow')
        self._machine.add_transition('on_yellow', 'implausible', 'yellow')

        # real transitions
        self._machine.add_transition('on_green', ['none', 'red'], 'green', after='green_go')
        self._machine.add_transition('on_green', ['red_yellow'], 'green')
        self._machine.add_transition('on_green', ['yellow'], 'implausible')

        self._machine.add_transition('on_red', ['yellow'], 'red')
        self._machine.add_transition('on_red', ['green', 'red_yellow'], 'implausible')
        self._machine.add_transition('on_red', ['none'], 'red', after='attention_red')

        self._machine.add_transition('on_yellow', ['none', 'green'], 'yellow', after='no_rush')
        self._machine.add_transition('on_yellow', ['red', 'red_yellow'], 'implausible')

        self._machine.add_transition('on_red_yellow', ['red', 'none'], 'red_yellow', after='ready_go')
        self._machine.add_transition('on_red_yellow', ['green', 'yellow'], 'implausible')

        self._machine.add_transition('on_reset', '*', 'none')

    def update_time(self):
        self._last_update_time = time.time()

    @property
    def last_update_time(self):
        return self._last_update_time

    def reset_sound(self):
        self._sound_track = None

    def green_go(self):
        self._sound_track = 'green'

    def attention_red(self):
        self._sound_track = 'red'

    def no_rush(self):
        self._sound_track = 'yellow'

    def ready_go(self):
        self._sound_track = 'red_yellow'

    @property
    def sound_track(self):
        return self._sound_track


class TrafficLightStateAdaptorWithSM(object):
    def __init__(self):
        self._state_machine = TrafficLightDetectionToSound()

        # do not distinguish left right
        self._state_to_trigger = {
            "green": self._state_machine.on_green,
            "red": self._state_machine.on_red,
            "yellow": self._state_machine.on_yellow,
            "red_yellow": self._state_machine.on_red_yellow,
            "green_left": self._state_machine.on_green,
            "red_left": self._state_machine.on_red,
            "green_right": self._state_machine.on_green,
            "red_right": self._state_machine.on_red,
            "side": lambda: None,
            "none": lambda: None,
        }

    def update(self, state):
        sound_track = None
        if not state:  # no detected valid traffic light
            if self._time_interval_since_last_update() > 1.5:
                self._state_machine.on_reset()
            return sound_track

        self._state_to_trigger[state]()
        sound_track = self._state_machine.sound_track

        return sound_track

    def _time_interval_since_last_update(self):
        return time.time() - self._state_machine.last_update_time
