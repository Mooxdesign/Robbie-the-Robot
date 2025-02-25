#!/usr/bin/env python3

import os
import sys
import time
import threading
import numpy as np
from typing import Dict, List, Tuple, Optional

class RobotVisualizer:
    """Visualizes robot state in simulation mode"""
    
    # Singleton instance
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(RobotVisualizer, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize visualizer"""
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        
        # Robot state
        self.motor_speeds = [0, 0]  # Left, Right
        self.head_position = [0, 0]  # Pan, Tilt
        self.arm_positions = [0, 0]  # Left, Right
        self.camera_frame = np.zeros((480, 640, 3))
        self.led_matrix = np.zeros((4, 8, 3))  # 8x4 RGB LED matrix
        self.audio_level = -100  # Audio level in dB
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        print("Robot visualizer initialized (simulation mode)")
            
    def set_audio_level(self, db_level: float):
        """Update audio level"""
        with self._lock:
            self.audio_level = max(-100, min(0, db_level))  # Clamp between -100 and 0 dB
            
    def set_led(self, x: int, y: int, r: int, g: int, b: int):
        """Set LED color"""
        with self._lock:
            self.led_matrix[y, x] = [r/255, g/255, b/255]
            # Print when setting all LEDs to same color (state change)
            target_color = np.array([r/255, g/255, b/255])
            if np.all(np.all(self.led_matrix == target_color, axis=2)):
                print(f"LED Matrix: RGB({r}, {g}, {b})")
            
    def clear_leds(self):
        """Clear all LEDs"""
        with self._lock:
            self.led_matrix.fill(0)
            print("LED Matrix: Cleared")
            
    def cleanup(self):
        """Clean up resources"""
        pass


def get_visualizer():
    """Get or create visualizer instance"""
    return RobotVisualizer()
