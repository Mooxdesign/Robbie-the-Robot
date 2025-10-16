from random import randint
import time
from modules.leds import LedsModule

def random_sparkles(leds: LedsModule, loop: bool = True):
    """Random Sparkles animation migrated from unicorn-hat example."""
    leds.is_animating = True
    leds.current_animation_state = {'currentAnimation': 'random_sparkles', 'loop': loop}
    width, height = leds.width, leds.height
    try:
        while leds.is_animating and loop:
            x = randint(0, width-1)
            y = randint(0, height-1)
            r = randint(0, 255)
            g = randint(0, 255)
            b = randint(0, 255)
            leds.set_pixel(x, y, r, g, b)
            leds.show()
    finally:
        leds.current_animation_state = None
