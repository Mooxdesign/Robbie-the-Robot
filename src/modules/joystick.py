#!/usr/bin/env python3

import threading
import time
from typing import Dict, Optional, Callable, List, Tuple
import pygame
import logging
DEADZONE = 0.10  # Hardcoded deadzone for stick axes (apply to indices 0..3 only)
logger = logging.getLogger(__name__)

class Joystick:
    """
    Handles game controller input for robot control
    """
    
    def __init__(self, 
                 joystick_id: int = 0,
                 debug: bool = False,
                 run_threaded: bool = True):
        """
        Initialize joystick module
        
        Args:
            joystick_id: ID of the joystick to use
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        self._run_threaded = run_threaded
        
            # Initialize pygame and joystick (joystick API only)
        try:
            pygame.init()
            pygame.joystick.init()
            # Get joystick
            self.joystick = pygame.joystick.Joystick(joystick_id)
            self.joystick.init()
            if self.debug:
                try:
                    name = self.joystick.get_name()
                    axes_n = self.joystick.get_numaxes()
                    btns_n = self.joystick.get_numbuttons()
                except Exception:
                    name, axes_n, btns_n = None, 0, 0
                logger.info(f"Initialized joystick: {name}")
                logger.info(f"Number of axes: {axes_n}")
                logger.info(f"Number of buttons: {btns_n}")
                
        except Exception as e:
            logger.exception(f"Failed to initialize joystick: {e}")
            self.joystick = None
            
        # Input state
        self.axis_values = {}  # Raw axis values
        self.button_values = {}  # Button states
        self.axis_handlers = {}  # Callbacks for axis changes
        self.button_handlers = {}  # Callbacks for button presses
        self._snapshot_cb = None  # Callback for full-state snapshots (axes, buttons)
        
        # Control thread
        self.is_running = False
        self.thread = None

        # Debug helpers
        self._last_debug_log_time = 0.0
        self._last_axes_snapshot: List[float] = []
        self._last_buttons_snapshot: List[bool] = []
        
        # Register cleanup
        import atexit
        atexit.register(self.cleanup)
        
    def start(self):
        """Start processing joystick input (threaded mode only)"""
        if not self.joystick:
            logger.warning("No joystick available")
            return
        if not self._run_threaded:
            # In no-thread mode, caller must call process_once()
            return
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._process_input, daemon=True)
            self.thread.start()
            if self.debug:
                logger.info("Started joystick processing")
                
    def stop(self):
        """Stop processing joystick input"""
        self.is_running = False
        if self.thread:
            self.thread.join()
            if self.debug:
                logger.info("Stopped joystick processing")
                
    def add_axis_handler(self, 
                        axis: int, 
                        handler: Callable[[float], None],
                        smooth: bool = True):
        """
        Add handler for axis changes
        
        Args:
            axis: Axis number
            handler: Function to call with axis value (-1.0 to 1.0)
            smooth: Apply smoothing to axis values
        """
        self.axis_handlers[axis] = {
            'handler': handler,
            'smooth': smooth,
            'last_value': 0.0
        }
        
    def add_button_handler(self,
                          button: int,
                          handler: Callable[[bool], None]):
        """
        Add handler for button presses
        
        Args:
            button: Button number
            handler: Function to call with button state
        """
        self.button_handlers[button] = handler

    def set_snapshot_callback(self, cb: Callable[[List[float], List[bool]], None]):
        """
        Register a callback that receives the full axes/buttons snapshot when they change.
        """
        self._snapshot_cb = cb
        
    def get_axis(self, axis: int) -> float:
        """Get current value of an axis"""
        return self.axis_values.get(axis, 0.0)
        
    def get_button(self, button: int) -> bool:
        """Get current state of a button"""
        return self.button_values.get(button, False)
        
    def _process_input(self):
        """Main input processing loop"""
        smoothing = 0.3  # Smoothing factor for axis values
        
        while self.is_running:
            self.process_once(smoothing)

            time.sleep(0.01)  # Prevent excessive CPU usage

    def process_once(self, smoothing: float = 0.3):
        """Process a single input tick: pump events, read axes/buttons, emit snapshot if changed."""
        # Process pygame events
        pygame.event.pump()
        with self._lock:
            # Process axes
            num_axes = self.joystick.get_numaxes()
            for i in range(num_axes):
                value = self.joystick.get_axis(i)
                # Apply deadzone only to stick axes (0..3)
                if i < 4 and abs(value) < DEADZONE:
                    value = 0.0
                # Store raw value
                self.axis_values[i] = value
                # Call handler if registered
                if i in self.axis_handlers:
                    handler = self.axis_handlers[i]
                    if handler['smooth']:
                        value = (value * (1 - smoothing) + handler['last_value'] * smoothing)
                        handler['last_value'] = value
                    handler['handler'](value)

            # Process buttons
            num_buttons = self.joystick.get_numbuttons()
            for i in range(num_buttons):
                value = bool(self.joystick.get_button(i))
                if value != self.button_values.get(i, False):
                    self.button_values[i] = value
                    if self.debug:
                        logger.info(f"[Joystick] button {i} {'down' if value else 'up'}")
                    if i in self.button_handlers:
                        self.button_handlers[i](value)

            # Periodic debug log of full axes snapshot
            if self.debug:
                import time as _t
                now = _t.time()
                if now - self._last_debug_log_time > 0.2:
                    total_axes = self.joystick.get_numaxes()
                    axes_list = [self.axis_values.get(j, 0.0) for j in range(total_axes)]
                    if axes_list != self._last_axes_snapshot:
                        logger.info(f"[Joystick] axes {axes_list}")
                        self._last_axes_snapshot = list(axes_list)
                    self._last_debug_log_time = now

            # Emit snapshot if changed
            total_axes = self.joystick.get_numaxes()
            axes_list = [self.axis_values.get(j, 0.0) for j in range(total_axes)]
            buttons_list = [self.button_values.get(j, False) for j in range(num_buttons)]
            if (axes_list != self._last_axes_snapshot) or (buttons_list != self._last_buttons_snapshot):
                self._last_axes_snapshot = list(axes_list)
                self._last_buttons_snapshot = list(buttons_list)
                if self._snapshot_cb:
                    if self.debug:
                        try:
                            logger.info(f"[Joystick][emit] axes={axes_list[:6]} (len={len(axes_list)}), buttons_on={[i for i,b in enumerate(buttons_list) if b]}")
                        except Exception:
                            pass
                    try:
                        self._snapshot_cb(self._last_axes_snapshot, self._last_buttons_snapshot)
                    except Exception:
                        pass
            
    def cleanup(self):
        """Clean up joystick resources"""
        self.stop()
        pygame.quit()
        if self.debug:
            logger.info("Joystick cleanup completed")
