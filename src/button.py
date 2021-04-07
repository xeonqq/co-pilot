import RPi.GPIO as GPIO

# will use pin 8
class Button(object):
    def __init__(self, pin):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
        GPIO.setup(self._pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def is_pressed(self):
        return GPIO.input(self._pin) == GPIO.LOW

    def add_pressed_cb(self, callback):
        GPIO.add_event_detect(
            self._pin, GPIO.FALLING, callback=callback, bouncetime=300
        )
