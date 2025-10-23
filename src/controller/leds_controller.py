import threading
from modules.leds import LedsModule
from modules.audio import AudioModule
from .leds_animations import LedsAnimations
import logging
from typing import Optional, Tuple, Callable, List

logger = logging.getLogger(__name__)

class LedsController:
    """Handles all LED control and pattern logic, delegating hardware to LedsModule."""
    def __init__(self, audio_module: AudioModule, brightness: float = 0.5, debug: bool = False):
        self.leds = LedsModule(brightness=brightness, debug=debug)
        self.debug = debug
        self._lock = threading.RLock()
        self.audio_module = audio_module
        self._animation_thread = None
        self._animation_stop_event = None
        self.current_animation_state = None
        self._api_update_callbacks: List[Callable[['LedsController'], None]] = []
        self._current_audio_level_db: float = -100.0 # Initialize with a very low dB value

        # Register internal callback for LedsModule updates
        self.leds.add_update_callback(self._on_led_module_update)

        # Register internal callback for AudioModule updates
        self.audio_module.add_output_audio_level_callback(self._on_audio_level_update)
        self.audio_module.start_monitoring()

    logger.info("[LEDS_CONTROLLER] _on_led_module_update method loaded.")
    def _on_led_module_update(self, leds_module: LedsModule):
        """Internal callback for LedsModule updates, triggers API callbacks."""
        for callback in self._api_update_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in API update callback: {e}")

    def _on_audio_level_update(self, audio_level_db: float):
        """Internal callback for AudioModule updates, stores the latest audio level."""
        self._current_audio_level_db = audio_level_db

    def set_color(self, r: int, g: int, b: int):
        self.stop_animation()
        self.leds.set_color(r, g, b)

    def set_all(self, r: int, g: int, b: int):
        self.stop_animation()
        self.leds.set_all(r, g, b)

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        self.stop_animation()
        self.leds.set_pixel(x, y, r, g, b)

    @staticmethod
    def _run_animation_thread(anim_func, leds_module, animation_name, leds_controller_instance, **kwargs):
        logger.debug(f"[LEDS_CONTROLLER] Entering animation thread target for '{animation_name}'.")
        try:
            # Pass the leds_controller_instance to the animation function if it needs it
            if 'audio_pulse' == animation_name:
                kwargs['leds_controller'] = leds_controller_instance
            anim_func(leds_module, **kwargs)
        except Exception as e:
            logger.error(f"[LEDS_CONTROLLER] Error in animation thread '{animation_name}': {e}", exc_info=True)

    def start_animation(self, animation_name: str, **kwargs):
        with self._lock:
            logger.info(f"[LEDS_CONTROLLER] start_animation called with: {animation_name}")
            self.stop_animation()

            anim_func = getattr(LedsAnimations, animation_name, None)
            if anim_func:
                logger.info(f"[LEDS_CONTROLLER] Animation function found: {animation_name}, starting thread.")
                self._animation_stop_event = threading.Event()
                self.current_animation_state = {'currentAnimation': animation_name, 'duration': kwargs.get('duration')}
                
                kwargs['stop_event'] = self._animation_stop_event
                
                self._animation_thread = threading.Thread(
                    target=LedsController._run_animation_thread,
                    args=(anim_func, self.leds, animation_name, self),
                    kwargs=kwargs,
                    daemon=True
                )
                self._animation_thread.start()
            else:
                logger.warning(f"[LEDS_CONTROLLER] Animation {animation_name} not found in LedsAnimations.")

    def stop_animation(self):
        with self._lock:
            if self._animation_stop_event:
                self._animation_stop_event.set()
            if self._animation_thread and self._animation_thread.is_alive():
                self._animation_thread.join(timeout=1)
            
            self._animation_thread = None
            self._animation_stop_event = None
            self.current_animation_state = None

    def cleanup(self):
        self.stop_animation()
        self.leds.cleanup()

    def add_update_callback(self, callback):
        """Pass through to LedsModule to register a callback for LED updates."""
        self.leds.add_update_callback(callback)

    def add_api_update_callback(self, callback: Callable[['LedsController'], None]):
        """Register a callback to be triggered when LED state changes for API updates."""
        self._api_update_callbacks.append(callback)
