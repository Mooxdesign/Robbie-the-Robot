import threading
import time
from typing import Callable, List, Dict, Any
import logging
import json

from modules.joystick import Joystick as JoystickModule

logger = logging.getLogger(__name__)

class JoystickController:
    """
    REPL-style joystick poller that reads axes/buttons in a single thread
    and publishes updates via a callback.
    """
    def __init__(self,
                 on_update: Callable[[dict], None],
                 joystick_id: int = 0,
                 poll_hz: float = 60.0,
                 debug: bool = False,
                 config: Dict[str, Any] = None) -> None:
        self.on_update = on_update
        self.joystick_id = joystick_id
        self.poll_dt = 1.0 / max(1.0, float(poll_hz))
        self.debug = debug
        self.config = config or {}

        self._thread: threading.Thread | None = None
        self._running = False
        self._jm: JoystickModule | None = None
        self._last_axes: List[float] | None = None
        self._last_buttons: List[bool] | None = None
        self._last_emit_ts: float = 0.0
        
        # Action handlers
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_action_handlers()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="JoystickController", daemon=True)
        self._thread.start()
        if self.debug:
            logger.info("[JoystickController] Started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            if self.debug:
                logger.info("[JoystickController] Stopped")

    def cleanup(self) -> None:
        self.stop()
        if self._jm:
            try:
                self._jm.cleanup()
            except Exception:
                pass

    def _run(self) -> None:
        # Create the existing joystick module in no-thread mode and drive it here
        try:
            jm = JoystickModule(joystick_id=self.joystick_id, debug=self.debug, run_threaded=False)
            jm.set_snapshot_callback(lambda axes, buttons: self._forward_snapshot(axes, buttons))
            
            # Register button actions and combinations from config
            self._register_button_actions(jm)
            self._register_button_combinations(jm)
            
            # Do not call jm.start(); we'll poll manually to ensure init+pump+read are in this thread
            self._jm = jm
        except Exception as e:
            if self.debug:
                logger.info(f"[JoystickController] Failed to init module: {e}")
            self._running = False
            return

        # Poll the module once per tick; this mirrors the REPL exactly in this thread
        import time
        while self._running:
            try:
                jm.process_once()
            except Exception:
                pass
            # keepalive: if we have a last snapshot, re-emit every 1s
            try:
                if self._last_axes is not None and (time.time() - self._last_emit_ts) > 1.0:
                    self._forward_snapshot(self._last_axes, self._last_buttons or [])
            except Exception:
                pass
            time.sleep(self.poll_dt)

    def _forward_snapshot(self, axes: List[float], buttons: List[bool]) -> None:
        try:
            self._last_axes = list(axes) if axes is not None else []
            self._last_buttons = list(buttons) if buttons is not None else []
            import time as _t
            self._last_emit_ts = _t.time()
            payload = {
                'joystick': {
                    'connected': bool(self._last_axes) or bool(self._last_buttons),
                    'axes': self._last_axes,
                    'buttons': self._last_buttons,
                }
            }
            self.on_update(payload)
        except Exception:
            pass
    
    def _register_default_action_handlers(self) -> None:
        """Register default action handlers"""
        self._action_handlers = {
            'confirm': self._handle_confirm,
            'cancel': self._handle_cancel,
            'wave': self._handle_wave,
            'dance': self._handle_dance,
            'look_left': self._handle_look_left,
            'look_right': self._handle_look_right,
            'reset_position': self._handle_reset_position,
            'emergency_stop': self._handle_emergency_stop,
            'center_head': self._handle_center_head,
            'calibrate': self._handle_calibrate,
            'shutdown': self._handle_shutdown,
            'toggle_voice': self._handle_toggle_voice,
            'save_position': self._handle_save_position,
            'load_position': self._handle_load_position,
        }
    
    def register_action_handler(self, action: str, handler: Callable) -> None:
        """Register a custom action handler"""
        self._action_handlers[action] = handler
    
    def _register_button_actions(self, jm: JoystickModule) -> None:
        """Register single button actions from config"""
        button_actions = self.config.get('joystick', {}).get('button_actions', {})
        for button_num, action_config in button_actions.items():
            if isinstance(button_num, str):
                button_num = int(button_num)
            action = action_config.get('action') if isinstance(action_config, dict) else action_config
            if action:
                jm.add_button_handler(button_num, lambda pressed, a=action: self._handle_button_action(a, pressed))
                if self.debug:
                    desc = action_config.get('description', '') if isinstance(action_config, dict) else ''
                    logger.info(f"[JoystickController] Registered button {button_num}: {action} - {desc}")
    
    def _register_button_combinations(self, jm: JoystickModule) -> None:
        """Register button combinations from config"""
        combinations = self.config.get('joystick', {}).get('button_combinations', {})
        for combo_str, combo_config in combinations.items():
            try:
                # Parse button list from string like "[4, 5]"
                buttons = json.loads(combo_str)
                action = combo_config.get('action')
                hold_time = combo_config.get('hold_time', 0.0)
                
                if action and buttons:
                    jm.add_combination_handler(
                        buttons=buttons,
                        handler=self._handle_combination_action,
                        action=action,
                        hold_time=hold_time
                    )
                    if self.debug:
                        desc = combo_config.get('description', '')
                        logger.info(f"[JoystickController] Registered combination {buttons}: {action} (hold={hold_time}s) - {desc}")
            except Exception as e:
                logger.error(f"Failed to register combination {combo_str}: {e}")
    
    def _handle_button_action(self, action: str, pressed: bool) -> None:
        """Handle single button action (only trigger on press, not release)"""
        if not pressed:
            return
        
        if self.debug:
            logger.info(f"[JoystickController] Button action: {action}")
        
        handler = self._action_handlers.get(action)
        if handler:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error handling button action '{action}': {e}")
        else:
            logger.warning(f"No handler registered for action: {action}")
    
    def _handle_combination_action(self, action: str) -> None:
        """Handle button combination action"""
        if self.debug:
            logger.info(f"[JoystickController] Combination action: {action}")
        
        handler = self._action_handlers.get(action)
        if handler:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error handling combination action '{action}': {e}")
        else:
            logger.warning(f"No handler registered for action: {action}")
    
    # Default action handlers (can be overridden by registering custom handlers)
    def _handle_confirm(self):
        logger.info("[Action] Confirm")
        self._send_action_event('confirm')
    
    def _handle_cancel(self):
        logger.info("[Action] Cancel")
        self._send_action_event('cancel')
    
    def _handle_wave(self):
        logger.info("[Action] Wave gesture")
        self._send_action_event('wave')
    
    def _handle_dance(self):
        logger.info("[Action] Dance routine")
        self._send_action_event('dance')
    
    def _handle_look_left(self):
        logger.info("[Action] Look left")
        self._send_action_event('look_left')
    
    def _handle_look_right(self):
        logger.info("[Action] Look right")
        self._send_action_event('look_right')
    
    def _handle_reset_position(self):
        logger.info("[Action] Reset position")
        self._send_action_event('reset_position')
    
    def _handle_emergency_stop(self):
        logger.info("[Action] Emergency stop")
        self._send_action_event('emergency_stop')
    
    def _handle_center_head(self):
        logger.info("[Action] Center head")
        self._send_action_event('center_head')
    
    def _handle_calibrate(self):
        logger.info("[Action] Calibrate servos")
        self._send_action_event('calibrate')
    
    def _handle_shutdown(self):
        logger.info("[Action] Shutdown")
        self._send_action_event('shutdown')
    
    def _handle_toggle_voice(self):
        logger.info("[Action] Toggle voice")
        self._send_action_event('toggle_voice')
    
    def _handle_save_position(self):
        logger.info("[Action] Save position")
        self._send_action_event('save_position')
    
    def _handle_load_position(self):
        logger.info("[Action] Load position")
        self._send_action_event('load_position')
    
    def _send_action_event(self, action: str) -> None:
        """Send action event through the update callback"""
        try:
            payload = {
                'joystick_action': {
                    'action': action,
                    'timestamp': time.time()
                }
            }
            self.on_update(payload)
        except Exception as e:
            logger.error(f"Failed to send action event: {e}")
