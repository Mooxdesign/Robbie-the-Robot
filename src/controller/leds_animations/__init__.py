import time
from typing import Tuple

from .rainbow import rainbow
from .rainbow_blinky import rainbow_blinky
from .random_blinky import random_blinky
from .random_sparkles import random_sparkles
from .snow import snow
from .vu_meter import audio_vu_meter
from .pulse_core import color_pulse_animation, rainbow_pulse_animation
from .audio_pulse import audio_pulse
from .solid import solid_color_animation
from .wave import wave_line_animation

class LedsAnimations:
    @staticmethod
    def rainbow(leds, stop_event, duration=None):
        return rainbow(leds, stop_event, duration=duration)

    @staticmethod
    def standby_pulse(leds, stop_event, duration=None):
        # Slow occasional pulse with gap for standby
        return LedsAnimations.color_pulse(leds, stop_event, 255, 220, 0, duration=duration, frequency=0.3, pulse_time=2)

    @staticmethod
    def solid_green(leds, stop_event, duration=None):
        # Wave green line for listening
        return wave_line_animation(leds, stop_event, 0, 255, 0, duration=duration, frequency=1.0)

    @staticmethod
    def solid_blue(leds, stop_event, duration=None):
        # Wave blue line for processing
        return wave_line_animation(leds, stop_event, 0, 0, 255, duration=duration, frequency=1.0)

    @staticmethod
    def rainbow_blinky(leds, stop_event, duration=None):
        return rainbow_blinky(leds, stop_event, duration=duration)

    @staticmethod
    def random_blinky(leds, stop_event, duration=None):
        return random_blinky(leds, stop_event, duration=duration)

    @staticmethod
    def random_sparkles(leds, stop_event, duration=None):
        return random_sparkles(leds, stop_event, duration=duration)

    @staticmethod
    def snow(leds, stop_event, duration=None):
        return snow(leds, stop_event, duration=duration)

    @staticmethod
    def audio_pulse(leds, stop_event, leds_controller, duration=None):
        return audio_pulse(leds, stop_event, leds_controller, duration=duration)

    @staticmethod
    def color_pulse(leds, stop_event, r, g, b, duration=None, frequency=1.0, pulse_time=0.5):
        return color_pulse_animation(leds, stop_event, r, g, b, duration=duration, frequency=frequency, pulse_time=pulse_time)

    @staticmethod
    def rainbow_pulse(leds, stop_event, duration=None, frequency=1.0, pulse_time=0.5):
        return rainbow_pulse_animation(leds, stop_event, duration=duration, frequency=frequency, pulse_time=pulse_time)
