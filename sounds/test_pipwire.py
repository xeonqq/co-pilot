from pipewire_python.controller import Controller

# [PLAYBACK]: normal way
audio_controller = Controller()
audio_controller.set_config(rate=384000,
                            channels=2,
                            _format='f64',
                            volume=0.98,
                            quality=4)
audio_controller.playback(audio_filename='en/red.wav')
print("blocking")
audio_controller.playback(audio_filename='en/green.wav')
