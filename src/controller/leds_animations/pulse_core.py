import time
import threading
from modules.leds import LedsModule
import math
import colorsys

def _pulse_core(
    leds: LedsModule,
    stop_event: threading.Event,
    duration: float,
    frequency: float,
    set_pixels_fn,
    pulse_time: float = 0.5  # duration of the pulse (seconds)
):
    start_time = time.time()
    cycle_time = 1.0 / frequency if frequency > 0 else 1.0
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        elapsed = time.time() - start_time
        cycle_phase = (elapsed % cycle_time) / cycle_time
        # If pulse_time >= cycle_time, pulse fills the cycle; else, gap between pulses
        if cycle_phase < (pulse_time / cycle_time):
            pulse_phase = cycle_phase * cycle_time / pulse_time
            brightness = 0.5 * (1 + math.sin(2 * math.pi * pulse_phase - math.pi/2))  # 0..1
        else:
            brightness = 0.0
        set_pixels_fn(leds, brightness)
        leds.show()
        time.sleep(0.01)

def color_pulse_animation(leds, stop_event, r, g, b, duration=None, frequency=1.0, pulse_time=0.5):
    def set_pixels(leds, brightness):
        leds.set_all(int(r * brightness), int(g * brightness), int(b * brightness))
    _pulse_core(leds, stop_event, duration, frequency, set_pixels, pulse_time=pulse_time)

def rainbow_pulse_animation(leds, stop_event, duration=None, frequency=1.0, pulse_time=0.5):
    width, height = leds.width, leds.height
    def set_pixels(leds, brightness):
        for y in range(height):
            for x in range(width):
                h = x / width
                s = 1.0
                v = brightness
                rgb = colorsys.hsv_to_rgb(h, s, v)
                leds.set_pixel(x, y, int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    _pulse_core(leds, stop_event, duration, frequency, set_pixels, pulse_time=pulse_time)
