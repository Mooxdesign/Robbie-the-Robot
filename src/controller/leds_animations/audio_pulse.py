import colorsys
import numpy as np
from modules.leds import LedsModule
import threading
import time
import logging

logger = logging.getLogger(__name__)

def make_gaussian(fwhm):
    x = np.arange(0, 8, 1, float)
    y = x[:, np.newaxis]
    x0, y0 = 3.5, 3.5
    gauss = np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)
    return gauss

def _audio_pulse_step(leds: LedsModule, audio_level_db: float):
    """
    Displays a pulsing rainbow effect on the LED matrix based on the audio level.
    The size of the pulse is controlled by the audio level.

    Args:
        leds: The LedsModule instance.
        audio_level_db: The audio level in decibels.
    """
    # Define the dB range and map it to the size of the Gaussian blob.
    min_db = -50.0

    # Add a threshold to prevent noise from showing up
    if audio_level_db < min_db:
        leds.set_all(0, 0, 0)
        leds.show()
        return

    max_db = -5.0
    normalized_level = (audio_level_db - min_db) / (max_db - min_db)
    normalized_level = max(0.0, min(1.0, normalized_level))  # Clamp between 0 and 1
    logger.info(f"[AUDIO_PULSE] Audio level: {audio_level_db:.2f} dB, Normalized: {normalized_level:.2f}")

    # Apply an exponential curve to make the animation less sensitive at lower volumes
    exponential_level = normalized_level ** 2
    logger.info(f"[AUDIO_PULSE] Exponential level: {exponential_level:.2f}")

    # Map the exponential level to the fwhm of the Gaussian
    # fwhm ranges from 1.0 (small dot) to 10.0 (fills the screen)
    fwhm = 1.0 + exponential_level * 9.0
    logger.info(f"[AUDIO_PULSE] FWHM: {fwhm:.2f}")

    gauss = make_gaussian(fwhm)

    width, height = leds.width, leds.height
    delta = 0 if height == width else 2

    for y in range(height):
        for x in range(width):
            h = 1.0 / (x + y + delta + 1)  # Hue from rainbow_blinky
            s = 0.8  # Saturation from rainbow_blinky
            v = gauss[x, y+delta] if height <= width else gauss[x+delta, y]
            logger.info(f"[AUDIO_PULSE] Pixel ({x},{y}) V: {v:.2f}")
            logger.info(f"[AUDIO_PULSE] Pixel ({x},{y}) HSV: ({h:.2f}, {s:.2f}, {v:.2f})")

            rgb = colorsys.hsv_to_rgb(h, s, v)
            logger.info(f"[AUDIO_PULSE] Pixel ({x},{y}) RGB (float): {rgb}")
            r = int(rgb[0] * 255.0)
            g = int(rgb[1] * 255.0)
            b = int(rgb[2] * 255.0)
            leds.set_pixel(x, y, r, g, b)
    logger.info(f"[AUDIO_PULSE] First pixel RGB: ({r}, {g}, {b})")
    leds.show()

def audio_pulse(leds: LedsModule, stop_event: threading.Event, leds_controller, duration: float = None):
    """Continuous loop for audio-reactive animation."""
    start_time = time.time()
    while not stop_event.is_set():
        if duration is not None and (time.time() - start_time) > duration:
            break
        _audio_pulse_step(leds, leds_controller._current_audio_level_db)
        time.sleep(0.05) # Update rate