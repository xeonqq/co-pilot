import unittest
import time

from .context import src
from src.state_machine import TrafficLightDetectionToSoundFull, TrafficLightStateAdaptorWithSM


class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self._state_machine = TrafficLightDetectionToSoundFull()

    def test_from_initial_to_green_to_green(self):
        self._state_machine.on_green()
        self.assertEqual("green", self._state_machine.sound_track)
        self._state_machine.on_green()
        self.assertEqual(None, self._state_machine.sound_track)
        self.assertEqual("green", self._state_machine.state)

    def test_from_red_to_red_yellow(self):
        self._state_machine.on_red()
        self.assertEqual('red', self._state_machine.sound_track)
        self._state_machine.on_red()
        self.assertEqual(None, self._state_machine.sound_track)
        self._state_machine.on_red_yellow()
        self.assertEqual('red_yellow', self._state_machine.sound_track)

    def test_from_green_to_red_yellow_implausible_case(self):
        self._state_machine.on_green()
        self._state_machine.on_green()
        self.assertEqual(None, self._state_machine.sound_track)
        self._state_machine.on_red_yellow()
        self.assertEqual(None, self._state_machine.sound_track)
        self.assertEqual('implausible', self._state_machine.state)
        self._state_machine.on_red_yellow()
        self.assertEqual(None, self._state_machine.sound_track)
        self.assertEqual('red_yellow', self._state_machine.state)

    def test_from_yellow_to_red(self):
        self._state_machine.on_green()
        self._state_machine.on_green()
        self.assertEqual(None, self._state_machine.sound_track)
        self._state_machine.on_yellow()
        self.assertEqual('yellow', self._state_machine.sound_track)
        self._state_machine.on_yellow()
        self.assertEqual(None, self._state_machine.sound_track)
        self._state_machine.on_red()
        self.assertEqual(None, self._state_machine.sound_track)


class TestStateAdatpor(unittest.TestCase):
    def setUp(self):
        self._state_adaptor = TrafficLightStateAdaptorWithSM('full')

    def test_state_adapter_with_cool_down_time(self):
        sound = self._state_adaptor.update('green')
        self.assertEqual('green', sound)
        for i in range(16):
            sound = self._state_adaptor.update(None)
            if i < 10:
                self.assertEqual('green', self._state_adaptor._state_machine.state)
            self.assertEqual(None, sound)
            time.sleep(0.1)
        self.assertEqual('none', self._state_adaptor._state_machine.state)

    def test_state_adapter_with_cool_down_time_with_same_state_interruption(self):
        sound = self._state_adaptor.update('green')
        self.assertEqual('green', sound)
        for i in range(16):
            if i < 10:
                sound = self._state_adaptor.update(None)
                self.assertEqual(None, sound)
            else:
                sound = self._state_adaptor.update('green')
                self.assertEqual(None, sound)
            time.sleep(0.1)

    def test_state_adapter_with_cool_down_time_with_different_state_interruption(self):
        sound = self._state_adaptor.update('green')
        self.assertEqual('green', sound)
        for i in range(5):
            if i < 4:
                sound = self._state_adaptor.update(None)
                self.assertEqual(None, sound)
            else:
                sound = self._state_adaptor.update('yellow')
                self.assertEqual('yellow', sound)
            time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()
