import math
import time
from modules.leds import LedsModule
import threading
import logging
logger = logging.getLogger(__name__)

def rainbow(leds: LedsModule, stop_event: threading.Event, duration: float = None):
    """Rainbow animation migrated from unicorn-hat example."""
    i = 0.0
    offset = 30
    width, height = leds.width, leds.height
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        i = i + 0.3
        for y in range(height):
            for x in range(width):
                r = (math.cos((x+i)/2.0) + math.cos((y+i)/2.0)) * 64.0 + 128.0
                g = (math.sin((x+i)/1.5) + math.sin((y+i)/2.0)) * 64.0 + 128.0
                b = (math.sin((x+i)/2.0) + math.cos((y+i)/1.5)) * 64.0 + 128.0
                r = max(0, min(255, r + offset))
                g = max(0, min(255, g + offset))
                b = max(0, min(255, b + offset))
                leds.set_pixel(x, y, int(r), int(g), int(b))
        logger.debug(f"[ANIMATION] Rainbow frame updated.")
        leds.show()
        time.sleep(0.01)
