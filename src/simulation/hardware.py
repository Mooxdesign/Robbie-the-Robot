#!/usr/bin/env python3

import os
import sys
import time
import threading
import numpy as np
from typing import Optional

from .visualizer import get_visualizer

# Global flag to control simulation output
VERBOSE = False

class SimulatedDCMotor:
    """Simulated DC motor for testing"""
    
    def __init__(self, channel: int):
        self.channel = channel
        self._throttle = 0.0
        self._last_throttle = 0.0
            
    @property
    def throttle(self) -> float:
        return self._throttle
    
    @throttle.setter
    def throttle(self, value: float):
        self._throttle = max(-1.0, min(1.0, value))
        if self._last_throttle != self._throttle:
            if VERBOSE:
                print(f"[SIM] DC Motor throttle set to {self._throttle:.2f}")
            self._last_throttle = self._throttle

class SimulatedServo:
    """Simulated servo for testing"""
    
    def __init__(self, channel: int):
        self.channel = channel
        self._angle = 0.0
        self._last_angle = None
        self._min_pulse = 500
        self._max_pulse = 2500

    def set_pulse_width_range(self, min_pulse: int, max_pulse: int):
        """Set pulse width range"""
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse
    
    @property
    def angle(self) -> float:
        return self._angle
    
    @angle.setter
    def angle(self, value: float):
        self._angle = max(0.0, min(180.0, value))
        if self._last_angle != self._angle:
            if VERBOSE:
                print(f"[SIM] Servo angle set to {self._angle:.1f}")
            self._last_angle = self._angle

class SimulatedMotorKit:
    """Simulated motor kit for testing"""
    
    def __init__(self, address: Optional[int] = None):
        self.motor1 = SimulatedDCMotor(0)  # Left motor
        self.motor2 = SimulatedDCMotor(1)  # Right motor

class SimulatedServoKit:
    """Simulated servo kit for testing"""
    
    def __init__(self, channels: int = 16):
        self.servo = []
        for i in range(channels):
            self.servo.append(SimulatedServo(i))

class SimulatedUnicornHATMini:
    """Simulated Unicorn HAT Mini for testing"""
    
    def __init__(self):
        """Initialize simulated LED matrix"""
        self.width = 8   # 8 LEDs wide
        self.height = 4  # 4 LEDs high
        self.brightness = 0.5
        # Internal buffer for LED state
        import numpy as np
        self._buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """
        Set pixel color
        
        Args:
            x: X position (0-7)
            y: Y position (0-3)
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
        """
        # Validate coordinates
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        # Scale by brightness
        r = int(r * self.brightness)
        g = int(g * self.brightness)
        b = int(b * self.brightness)
        self._buffer[y, x] = [r, g, b]
    
    def set_all(self, r: int, g: int, b: int):
        """Set all pixels to color"""
        for y in range(self.height):
            for x in range(self.width):
                self.set_pixel(x, y, r, g, b)
    
    def clear(self):
        """Clear all pixels"""
        self._buffer.fill(0)
    
    def show(self):
        """Update display - not needed in simulation"""
        pass
    
    def set_brightness(self, brightness: float):
        """Set LED brightness"""
        self.brightness = max(0.0, min(1.0, brightness))

class SimulatedUnicornHAT:
    """Simulated LED matrix for testing"""
    
    def __init__(self):
        self.width = 17
        self.height = 7
        self._buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._lock = threading.Lock()
        
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set pixel color"""
        with self._lock:
            if 0 <= x < self.width and 0 <= y < self.height:
                self._buffer[y, x] = [r, g, b]
    
    def clear(self):
        """Clear display"""
        with self._lock:
            self._buffer.fill(0)
    
    def show(self):
        """Update display"""
        pass  # No need to do anything in simulation

class SimulatedCamera:
    """Simulated camera for testing"""
    
    def __init__(self):
        self.resolution = (640, 480)
        self._frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self._visualizer = get_visualizer()
        
    def capture(self, output, format='rgb'):
        """Capture frame"""
        # Create a moving pattern for testing
        t = time.time()
        x = int((np.sin(t) + 1) * 320)
        y = int((np.cos(t) + 1) * 240)
        
        # Clear frame
        self._frame.fill(0)
        
        # Draw a moving circle
        for i in range(-10, 11):
            for j in range(-10, 11):
                if i*i + j*j <= 100:  # Circle of radius 10
                    px = x + i
                    py = y + j
                    if 0 <= px < 640 and 0 <= py < 480:
                        self._frame[py, px] = [255, 128, 0]  # Orange dot
                
        # Save to output
        output.save('dummy.jpg')  # Dummy save for simulation
