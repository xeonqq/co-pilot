import RPi.GPIO as GPIO

# will use pin 10
class Led(object):
    def __init__(self, pin):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
        GPIO.setup(self._pin, GPIO.OUT, initial=GPIO.LOW)
        self._state = GPIO.LOW

    def toggle(self):
        self._state = GPIO.LOW if self._state == GPIO.HIGH else GPIO.HIGH
        GPIO.output(self._pin, self._state)

    def on(self):
        GPIO.output(self._pin, GPIO.HIGH)
        self._state = GPIO.HIGH

    def off(self):
        GPIO.output(self._pin, GPIO.LOW)
        self._state = GPIO.LOW
