import time
import threading
import math
from modules.leds import LedsModule

def solid_color_animation(
    leds: LedsModule,
    stop_event: threading.Event,
    r: int,
    g: int,
    b: int,
    duration: float = None,
    pulse_speed: float = 1.0
):
    """
    Solid color animation with pulsing brightness.
    pulse_speed: 1.0 = normal, <1.0 = slower, >1.0 = faster
    """
    start_time = time.time()
    base_brightness = 0 # 0.2
    pulse_range = 1 # 0.8
    pulse_period = 2.0 / pulse_speed  # seconds for a full cycle
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        t = (time.time() - start_time) % pulse_period
        phase = t / pulse_period
        brightness = base_brightness + pulse_range * (0.5 * (1 + math.sin(2 * math.pi * phase - math.pi/2)))
        leds.set_all(int(r * brightness), int(g * brightness), int(b * brightness))
        leds.show()
        time.sleep(0.05)
