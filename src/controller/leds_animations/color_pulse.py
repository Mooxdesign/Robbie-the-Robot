import time
import threading
from modules.leds import LedsModule

def color_pulse_animation(
    leds: LedsModule,
    stop_event: threading.Event,
    r: int,
    g: int,
    b: int,
    duration: float = None,
    frequency: float = 1.0
):
    """
    Pulse the entire matrix in a single color (colorable), smoothly bright/dim.
    frequency: number of pulses per second.
    """
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        elapsed = time.time() - start_time
        phase = (elapsed * frequency) % 1.0
        brightness = 0.5 * (1 + math.sin(2 * math.pi * phase - math.pi/2))  # 0..1
        leds.set_all(int(r * brightness), int(g * brightness), int(b * brightness))
        leds.show()
        time.sleep(0.01)
