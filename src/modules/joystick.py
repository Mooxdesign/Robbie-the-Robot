#!/usr/bin/env python3

import threading
import time
from typing import Dict, Optional, Callable, List, Tuple
import pygame
import logging
logger = logging.getLogger(__name__)

class Joystick:
    """
    Handles game controller input for robot control
    """
    
    def __init__(self, 
                 joystick_id: int = 0,
                 deadzone: float = 0.1,
                 debug: bool = False):
        """
        Initialize joystick module
        
        Args:
            joystick_id: ID of the joystick to use
            deadzone: Minimum absolute value for axis input
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        self.deadzone = deadzone
        
        # Initialize pygame and joystick
        try:
            pygame.init()
            pygame.joystick.init()
            
            # Get joystick
            self.joystick = pygame.joystick.Joystick(joystick_id)
            self.joystick.init()
            
            if self.debug:
                logger.info(f"Initialized joystick: {self.joystick.get_name()}")
                logger.info(f"Number of axes: {self.joystick.get_numaxes()}")
                logger.info(f"Number of buttons: {self.joystick.get_numbuttons()}")
                
        except Exception as e:
            logger.exception(f"Failed to initialize joystick: {e}")
            self.joystick = None
            
        # Input state
        self.axis_values = {}  # Raw axis values
        self.button_values = {}  # Button states
        self.axis_handlers = {}  # Callbacks for axis changes
        self.button_handlers = {}  # Callbacks for button presses
        
        # Control thread
        self.is_running = False
        self.thread = None
        
        # Register cleanup
        import atexit
        atexit.register(self.cleanup)
        
    def start(self):
        """Start processing joystick input"""
        if not self.joystick:
            logger.warning("No joystick available")
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
            # Process pygame events
            pygame.event.pump()
            
            with self._lock:
                # Process axes
                for i in range(self.joystick.get_numaxes()):
                    value = self.joystick.get_axis(i)
                    
                    # Apply deadzone
                    if abs(value) < self.deadzone:
                        value = 0.0
                        
                    # Store raw value
                    self.axis_values[i] = value
                    
                    # Call handler if registered
                    if i in self.axis_handlers:
                        handler = self.axis_handlers[i]
                        if handler['smooth']:
                            # Apply smoothing
                            value = (value * (1 - smoothing) + 
                                   handler['last_value'] * smoothing)
                            handler['last_value'] = value
                        handler['handler'](value)
                        
                # Process buttons
                for i in range(self.joystick.get_numbuttons()):
                    value = bool(self.joystick.get_button(i))
                    
                    # Only trigger on state change
                    if value != self.button_values.get(i, False):
                        self.button_values[i] = value
                        if i in self.button_handlers:
                            self.button_handlers[i](value)
                            
            time.sleep(0.01)  # Prevent excessive CPU usage
            
    def cleanup(self):
        """Clean up joystick resources"""
        self.stop()
        pygame.quit()
        if self.debug:
            logger.info("Joystick cleanup completed")
