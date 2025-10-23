import colorsys
import time
import numpy as np
from modules.leds import LedsModule
import threading

def rainbow_blinky(leds: LedsModule, stop_event: threading.Event, duration: float = None):
    """Rainbow Blinky animation migrated from unicorn-hat example."""
    import logging
    logger = logging.getLogger(__name__)
    width, height = leds.width, leds.height
    delta = 0 if height == width else 2
    def make_gaussian(fwhm):
        x = np.arange(0, 8, 1, float)
        y = x[:, np.newaxis]
        x0, y0 = 3.5, 3.5
        gauss = np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)
        return gauss
    logger.info('[ANIMATION] rainbow_blinky thread started')
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        for z in list(range(1, 10)[::-1]) + list(range(1, 10)):
            if stop_event.is_set():
                break
            fwhm = 5.0 / z
            gauss = make_gaussian(fwhm)
            start = time.time()
            for y in range(height):
                for x in range(width):
                    h = 1.0 / (x + y + delta + 1)
                    s = 0.8
                    v = gauss[x, y+delta] if height <= width else gauss[x+delta, y]
                    rgb = colorsys.hsv_to_rgb(h, s, v)
                    r = int(rgb[0]*255.0)
                    g = int(rgb[1]*255.0)
                    b = int(rgb[2]*255.0)
                    leds.set_pixel(x, y, r, g, b)
            leds.show()
            t = time.time() - start
            if t < 0.04:
                time.sleep(0.04 - t)
    logger.info('[ANIMATION] rainbow_blinky thread exiting')
