import colorsys
import time
import numpy as np
from modules.leds import LedsModule
import threading

def random_blinky(leds: LedsModule, stop_event: threading.Event, duration: float = None):
    """Random Blinky animation migrated from unicorn-hat example."""
    width, height = leds.width, leds.height
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
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
