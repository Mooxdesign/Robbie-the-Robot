import colorsys
import time
import numpy as np
from modules.leds import LedsModule

def random_blinky(leds: LedsModule, loop: bool = True):
    """Random Blinky animation migrated from unicorn-hat example."""
    leds.is_animating = True
    leds.current_animation_state = {'currentAnimation': 'random_blinky', 'loop': loop}
    width, height = leds.width, leds.height
    try:
        while leds.is_animating and loop:
            rand_mat = np.random.rand(width, height)
            for y in range(height):
                for x in range(width):
                    h = 0.1 * rand_mat[x, y]
                    s = 0.8
                    v = rand_mat[x, y]
                    rgb = colorsys.hsv_to_rgb(h, s, v)
                    r = int(rgb[0]*255.0)
                    g = int(rgb[1]*255.0)
                    b = int(rgb[2]*255.0)
                    leds.set_pixel(x, y, r, g, b)
            leds.show()
            time.sleep(0.01)
    finally:
        leds.current_animation_state = None
