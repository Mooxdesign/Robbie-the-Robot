#!/usr/bin/env python3

import threading
import time
from typing import Dict, Optional, Callable, List, Tuple, Set
import pygame
import logging
import json
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
        
            # Initialize ONLY the joystick subsystem, not audio
            # pygame.init() would initialize audio mixer which locks the audio device
        try:
            # Only init display and joystick, skip audio mixer
            pygame.display.init()
            pygame.joystick.init()
            # Validate joystick id and get joystick
            count = pygame.joystick.get_count()
            if count == 0:
                logger.warning("No joystick devices detected")
                self.joystick = None
            else:
                if joystick_id < 0 or joystick_id >= count:
                    logger.warning(f"Requested joystick_id {joystick_id} out of range (0..{count-1}), defaulting to 0")
                    joystick_id = 0
                self.joystick = pygame.joystick.Joystick(joystick_id)
            if self.joystick is not None:
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
        
        # Button combination tracking
        self.combination_handlers = {}  # Callbacks for button combinations
        self._active_combinations = {}  # Track active combinations and their start times
        self._triggered_combinations = set()  # Track which combinations have been triggered
        
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
    
    def add_combination_handler(self,
                               buttons: List[int],
                               handler: Callable[[str], None],
                               action: str,
                               hold_time: float = 0.0):
        """
        Add handler for button combinations
        
        Args:
            buttons: List of button numbers that must be pressed together
            handler: Function to call with action name when combination is triggered
            action: Action name to pass to handler
            hold_time: Time in seconds buttons must be held before triggering
        """
        combo_key = tuple(sorted(buttons))
        self.combination_handlers[combo_key] = {
            'handler': handler,
            'action': action,
            'hold_time': hold_time,
            'buttons': buttons
        }
        
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
        # Detect hot-unplug: if we had a joystick but now count==0, emit disconnect
        try:
            dev_count = pygame.joystick.get_count()
        except Exception:
            dev_count = -1
        if self.joystick and dev_count == 0:
            if self.debug:
                logger.info("[Joystick] Device unplugged")
            self.joystick = None
            self.axis_values = {}
            self.button_values = {}
            self._last_axes_snapshot = []
            self._last_buttons_snapshot = []
            if self._snapshot_cb:
                try:
                    self._snapshot_cb([], [])
                except Exception:
                    pass
            return
        if not self.joystick:
            # Hot-plug detection: try to (re)initialize when a device appears
            try:
                count = pygame.joystick.get_count()
            except Exception:
                count = 0
            if count > 0:
                try:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    if self.debug:
                        try:
                            name = self.joystick.get_name()
                            axes_n = self.joystick.get_numaxes()
                            btns_n = self.joystick.get_numbuttons()
                        except Exception:
                            name, axes_n, btns_n = None, 0, 0
                        logger.info(f"[Joystick] Hot-plugged: {name} | axes={axes_n} buttons={btns_n}")
                    # Reset state and force an initial snapshot
                    try:
                        axes_n = self.joystick.get_numaxes()
                        btns_n = self.joystick.get_numbuttons()
                    except Exception:
                        axes_n, btns_n = 0, 0
                    self.axis_values = {i: 0.0 for i in range(axes_n)}
                    self.button_values = {i: False for i in range(btns_n)}
                    self._last_axes_snapshot = []  # force emit
                    self._last_buttons_snapshot = []
                    if self._snapshot_cb:
                        try:
                            self._snapshot_cb([0.0]*axes_n, [False]*btns_n)
                        except Exception:
                            pass
                except Exception:
                    # Leave joystick as None and return until next tick
                    return
            else:
                return
        with self._lock:
            # Process axes
            try:
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
                
                # Process button combinations
                self._process_combinations()

                # Process hats (D-pad). Represent each hat as 4 virtual buttons: [up, down, left, right]
                virtual_hat_buttons = []
                try:
                    num_hats = self.joystick.get_numhats()
                except Exception:
                    num_hats = 0
                for h in range(num_hats):
                    try:
                        hx, hy = self.joystick.get_hat(h)
                    except Exception:
                        hx, hy = 0, 0
                    # up, down, left, right
                    virtual_hat_buttons.extend([
                        bool(hy > 0),
                        bool(hy < 0),
                        bool(hx < 0),
                        bool(hx > 0),
                    ])
            except Exception:
                # Treat as device loss
                if self.debug:
                    logger.info("[Joystick] Read failed, assuming disconnect")
                self.joystick = None
                self.axis_values = {}
                self.button_values = {}
                self._last_axes_snapshot = []
                self._last_buttons_snapshot = []
                if self._snapshot_cb:
                    try:
                        self._snapshot_cb([], [])
                    except Exception:
                        pass
                return

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
            if virtual_hat_buttons:
                buttons_list = buttons_list + virtual_hat_buttons
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
            
    def _process_combinations(self):
        """Check for active button combinations and trigger handlers"""
        if not self.combination_handlers:
            return
        
        current_time = time.time()
        pressed_buttons = {btn for btn, state in self.button_values.items() if state}
        
        # Check each registered combination
        for combo_key, combo_info in self.combination_handlers.items():
            combo_set = set(combo_key)
            
            # Check if all buttons in combination are pressed
            if combo_set.issubset(pressed_buttons):
                # Combination is active
                if combo_key not in self._active_combinations:
                    # New combination press
                    self._active_combinations[combo_key] = current_time
                    if self.debug:
                        logger.info(f"[Joystick] Combination started: {list(combo_key)}")
                else:
                    # Check if hold time has been met
                    hold_duration = current_time - self._active_combinations[combo_key]
                    if hold_duration >= combo_info['hold_time'] and combo_key not in self._triggered_combinations:
                        # Trigger the combination
                        self._triggered_combinations.add(combo_key)
                        if self.debug:
                            logger.info(f"[Joystick] Combination triggered: {list(combo_key)} -> {combo_info['action']}")
                        try:
                            combo_info['handler'](combo_info['action'])
                        except Exception as e:
                            logger.error(f"Error in combination handler: {e}")
            else:
                # Combination is no longer active
                if combo_key in self._active_combinations:
                    del self._active_combinations[combo_key]
                    if combo_key in self._triggered_combinations:
                        self._triggered_combinations.remove(combo_key)
    
    def cleanup(self):
        """Clean up joystick resources"""
        self.stop()
        pygame.quit()
        if self.debug:
            logger.info("Joystick cleanup completed")
