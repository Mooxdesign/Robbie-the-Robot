from random import randint
import time
from modules.leds import LedsModule
import threading

def random_sparkles(leds: LedsModule, stop_event: threading.Event, duration: float = None):
    """Random Sparkles animation migrated from unicorn-hat example."""
    width, height = leds.width, leds.height
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        x = randint(0, width-1)
        y = randint(0, height-1)
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
        # Ensure at least one component is 255 for brightness
        if r < 255 and g < 255 and b < 255:
            choice = randint(0, 2) # 0 for r, 1 for g, 2 for b
            if choice == 0:
                r = 255
            elif choice == 1:
                g = 255
            else:
                b = 255
        leds.set_pixel(x, y, r, g, b)
        leds.show()
        time.sleep(0.01)
