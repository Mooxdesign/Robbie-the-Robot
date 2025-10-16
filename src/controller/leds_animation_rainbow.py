import math
import time
from modules.leds import LedsModule

def rainbow(leds: LedsModule, loop: bool = True):
    """Rainbow animation migrated from unicorn-hat example."""
    leds.is_animating = True
    leds.current_animation_state = {'currentAnimation': 'rainbow', 'loop': loop}
    i = 0.0
    offset = 30
    width, height = leds.width, leds.height
    try:
        while leds.is_animating and (loop or i == 0):
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
            leds.show()
            time.sleep(0.01)
    finally:
        leds.current_animation_state = None
