import threading
from modules.leds import LedsModule
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class LedsController:
    """Handles all LED control and pattern logic, delegating hardware to LedsModule."""
    def __init__(self, brightness: float = 0.5, debug: bool = False):
        self.leds = LedsModule(brightness=brightness, debug=debug)
        self.debug = debug
        self._lock = threading.Lock()

    def set_color(self, r: int, g: int, b: int):
        self.leds.set_color(r, g, b)

    def set_all(self, r: int, g: int, b: int):
        self.leds.set_all(r, g, b)

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        self.leds.set_pixel(x, y, r, g, b)

    def start_animation(self, animation_name: str, **kwargs):
        logger.info(f"[LEDS_CONTROLLER] start_animation called with: {animation_name}")
        from .leds_animations import LedsAnimations
        self.stop_animation()
        anim = getattr(LedsAnimations, animation_name, None)
        if anim:
            logger.info(f"[LEDS_CONTROLLER] Animation function found: {animation_name}, starting thread.")
            def run_anim():
                anim(self.leds, **kwargs)
            self._animation_thread = threading.Thread(target=run_anim, daemon=True)
            self._animation_thread.start()
        else:
            logger.warning(f"[LEDS_CONTROLLER] Animation {animation_name} not found in LedsAnimations.")

    def stop_animation(self):
        self.leds.is_animating = False
        if hasattr(self, '_animation_thread') and self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1)
        self.leds.stop_animation()

    def cleanup(self):
        self.leds.cleanup()
