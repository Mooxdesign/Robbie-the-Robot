import time
import threading
import math
from modules.leds import LedsModule

def wave_line_animation(
    leds: LedsModule,
    stop_event: threading.Event,
    r: int,
    g: int,
    b: int,
    duration: float = None,
    frequency: float = 1.0
):
    """
    Animate a vertical line of the given color moving left to right across the matrix.
    frequency: number of full left-to-right cycles per second.
    """
    width, height = leds.width, leds.height
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        elapsed_seconds = time.time() - start_time
        cycle_phase = (elapsed_seconds * frequency) % 1.0
        current_column_float = cycle_phase * width
        leds.set_all(0, 0, 0)
        blend_width = 5  # number of columns to blend for smoothness
        for offset in range(-blend_width, blend_width+1):
            blend_column = int((current_column_float + offset) % width)
            distance = abs((current_column_float - blend_column + width) % width)
            if distance > width/2:
                distance = width - distance
            blend_factor = 0.5 * (1 + math.cos(math.pi * distance / (blend_width+1))) if distance <= blend_width else 0
            for y in range(height):
                leds.set_pixel(blend_column, y, int(r * blend_factor), int(g * blend_factor), int(b * blend_factor))
        leds.show()
        time.sleep(0.01)
