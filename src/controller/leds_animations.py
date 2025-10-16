import time
from typing import Tuple

from .leds_animation_rainbow import rainbow
from .leds_animation_rainbow_blinky import rainbow_blinky
from .leds_animation_random_blinky import random_blinky
from .leds_animation_random_sparkles import random_sparkles
from .leds_animation_snow import snow

class LedsAnimations:
    @staticmethod
    def rainbow(leds, loop=True):
        return rainbow(leds, loop=loop)

    @staticmethod
    def rainbow_blinky(leds, loop=True):
        return rainbow_blinky(leds, loop=loop)

    @staticmethod
    def random_blinky(leds, loop=True):
        return random_blinky(leds, loop=loop)

    @staticmethod
    def random_sparkles(leds, loop=True):
        return random_sparkles(leds, loop=loop)

    @staticmethod
    def snow(leds, loop=True):
        return snow(leds, loop=loop)
