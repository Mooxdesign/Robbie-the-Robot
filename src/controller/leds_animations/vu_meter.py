import math
from modules.leds import LedsModule

def audio_vu_meter(leds: LedsModule, audio_level_db: float):
    """
    Displays a VU meter on the LED matrix based on the audio level in dB.
    The VU meter will be a vertical bar graph.

    Args:
        leds: The LedsModule instance.
        audio_level_db: The audio level in decibels.
    """
    if not leds.is_animating:
        leds.is_animating = True

    # Clear the display first
    leds.set_all(0, 0, 0)

    # Define the dB range. Assume a range from -60 dB (silent) to 0 dB (max).
    min_db = -50.0
    max_db = -5.0

    # Normalize the dB level to a 0-1 range
    normalized_level = (audio_level_db - min_db) / (max_db - min_db)
    normalized_level = max(0.0, min(1.0, normalized_level))  # Clamp between 0 and 1

    # Map the normalized level to the number of rows to light up
    num_rows_to_light = int(normalized_level * leds.height)

    # Light up the pixels
    for y in range(num_rows_to_light):
        # Simple green to red gradient
        if y < leds.height * 0.5:
            color = (0, 255, 0)  # Green
        elif y < leds.height * 0.8:
            color = (255, 255, 0)  # Yellow
        else:
            color = (255, 0, 0)  # Red
        
        for x in range(leds.width):
            leds.set_pixel(x, y, *color)

    leds.show()
