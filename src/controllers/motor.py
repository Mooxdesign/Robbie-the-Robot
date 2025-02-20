#!/usr/bin/env python3

import os
import sys
import time
import threading
import numpy as np
from typing import Optional, Dict, Tuple

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import Raspberry Pi specific libraries
try:
    import board
    from adafruit_motorkit import MotorKit
    from adafruit_servokit import ServoKit
    import smbus
    IS_RASPBERRY_PI = True
except ImportError:
    from src.simulation.hardware import (
        SimulatedMotorKit as MotorKit,
        SimulatedServoKit as ServoKit
    )
    IS_RASPBERRY_PI = False
    print("Running motor controller in simulation mode")

from src.config import Config

class MotorController:
    """
    Unified motor controller for both DC motors and servos.
    Handles acceleration limiting and thread safety.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize motor controller
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        
        # DC motor settings
        self.max_speed = config.get('motor', 'dc_motors', 'max_speed', default=1.0)
        self.acceleration = config.get('motor', 'dc_motors', 'acceleration', default=0.1)
        self.update_rate = config.get('motor', 'dc_motors', 'update_rate', default=50)
        
        # Initialize hardware
        try:
            if IS_RASPBERRY_PI:
                self.motor_kit = MotorKit(i2c=board.I2C())
                self.servo_kit = ServoKit(channels=16)
            else:
                self.motor_kit = MotorKit()
                self.servo_kit = ServoKit()
                
            if self.debug:
                print("Motor controller initialized")
                
        except Exception as e:
            print(f"Failed to initialize motor controller: {e}")
            self.motor_kit = None
            self.servo_kit = None
            
        # Motor state
        self.left_speed = 0
        self.right_speed = 0
        self.target_left = 0
        self.target_right = 0
        
        # Start update thread
        self.is_running = True
        self.update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self.update_thread.start()
        
    def set_motor_speeds(self, left: float, right: float):
        """
        Set target speeds for DC motors
        
        Args:
            left: Left motor speed (-1 to 1)
            right: Right motor speed (-1 to 1)
        """
        with self._lock:
            self.target_left = max(min(left, self.max_speed), -self.max_speed)
            self.target_right = max(min(right, self.max_speed), -self.max_speed)
            
            # Set speeds immediately in simulation mode
            if not IS_RASPBERRY_PI:
                self.left_speed = self.target_left
                self.right_speed = self.target_right
                if self.motor_kit:
                    self.motor_kit.motor1.throttle = self.left_speed
                    self.motor_kit.motor2.throttle = self.right_speed

    def stop(self):
        """Stop all motors"""
        self.set_motor_speeds(0, 0)
        
    def move_head(self, pan: Optional[float] = None, tilt: Optional[float] = None):
        """
        Move head servos
        
        Args:
            pan: Pan angle in degrees (-90 to 90)
            tilt: Tilt angle in degrees (-45 to 45)
        """
        if not self.servo_kit:
            return
            
        with self._lock:
            # Set pan servo (0)
            if pan is not None:
                # Convert to 0-180 range
                angle = (pan + 90)  # -90 -> 0, 90 -> 180
                self.servo_kit.servo[0].angle = angle
                
            # Set tilt servo (1)
            if tilt is not None:
                # Convert to 0-180 range, but limit to -45 to 45
                angle = (tilt + 45) * 2  # -45 -> 0, 45 -> 180
                self.servo_kit.servo[1].angle = angle
                
    def move_arm(self, side: str, position: float):
        """
        Move arm servo
        
        Args:
            side: 'left' or 'right'
            position: Position from 0 to 1
        """
        if not self.servo_kit:
            return
            
        with self._lock:
            # Convert 0-1 to 0-180
            angle = position * 180
            
            if side.lower() == 'left':
                self.servo_kit.servo[2].angle = angle
            else:
                self.servo_kit.servo[3].angle = angle
        
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()
            
        # Stop motors
        if self.motor_kit:
            self.motor_kit.motor1.throttle = 0
            self.motor_kit.motor2.throttle = 0
            
    def _update_loop(self):
        """Update motor speeds with acceleration limiting"""
        last_update = time.time()
        
        while self.is_running:
            current_time = time.time()
            dt = current_time - last_update
            last_update = current_time
            
            # Update speeds with acceleration limiting
            with self._lock:
                # Left motor
                error = self.target_left - self.left_speed
                if abs(error) > self.acceleration * dt:
                    self.left_speed += self.acceleration * dt * np.sign(error)
                else:
                    self.left_speed = self.target_left
                    
                # Right motor
                error = self.target_right - self.right_speed
                if abs(error) > self.acceleration * dt:
                    self.right_speed += self.acceleration * dt * np.sign(error)
                else:
                    self.right_speed = self.target_right
                    
                # Set motor speeds
                if self.motor_kit:
                    self.motor_kit.motor1.throttle = self.left_speed
                    self.motor_kit.motor2.throttle = self.right_speed
                    
            # Sleep to maintain update rate
            time.sleep(1 / self.update_rate)
