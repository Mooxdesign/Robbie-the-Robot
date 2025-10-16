import colorsys
import time
import numpy as np
from modules.leds import LedsModule

def rainbow_blinky(leds: LedsModule, loop: bool = True):
    """Rainbow Blinky animation migrated from unicorn-hat example."""
    import logging
    logger = logging.getLogger(__name__)
    leds.is_animating = True
    leds.current_animation_state = {'currentAnimation': 'rainbow_blinky', 'loop': loop}
    width, height = leds.width, leds.height
    delta = 0 if height == width else 2
    def make_gaussian(fwhm):
        x = np.arange(0, 8, 1, float)
        y = x[:, np.newaxis]
        x0, y0 = 3.5, 3.5
        gauss = np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)
        return gauss
    try:
        logger.info('[ANIMATION] rainbow_blinky thread started')
        while leds.is_animating and loop:
            for z in list(range(1, 10)[::-1]) + list(range(1, 10)):
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
                logger.info(f'[ANIMATION] Frame shown, first pixel: {leds.buffer[0,0]}')
                t = time.time() - start
                if t < 0.04:
                    time.sleep(0.04 - t)
    finally:
        logger.info('[ANIMATION] rainbow_blinky thread exiting')
        leds.current_animation_state = None
