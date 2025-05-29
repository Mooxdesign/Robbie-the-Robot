#!/usr/bin/env python3

import sys
import os
import time
import threading
from typing import Optional, Dict, Tuple

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from utils.hardware import MOTORS_AVAILABLE, SERVOS_AVAILABLE

if MOTORS_AVAILABLE or SERVOS_AVAILABLE:
    import board
    from adafruit_motorkit import MotorKit
    from adafruit_servokit import ServoKit
    print("Motor/servo hardware detected")
else:
    print("No motor/servo hardware detected - running in simulation mode")
    from simulation.hardware import (
        SimulatedMotorKit as MotorKit,
        SimulatedServoKit as ServoKit
    )

class MotorModule:
    """
    Unified motor controller for both DC motors and servos.
    Handles acceleration limiting and thread safety.
    """
    
    def __init__(self, debug: bool = False):
        self._left_arm_position = 0.0
        self._right_arm_position = 0.0
        self._head_pan = None
        self._head_tilt = None
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
            if MOTORS_AVAILABLE or SERVOS_AVAILABLE:
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
            if not (MOTORS_AVAILABLE or SERVOS_AVAILABLE):
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
                self._head_pan = pan
            # Set tilt servo (1)
            if tilt is not None:
                # Convert to 0-180 range, but limit to -45 to 45
                angle = (tilt + 45) * 2  # -45 -> 0, 45 -> 180
                self.servo_kit.servo[1].angle = angle
                self._head_tilt = tilt
                
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
                self._left_arm_position = position
            else:
                self.servo_kit.servo[3].angle = angle
                self._right_arm_position = position
        
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()
            
        # Stop motors
        if self.motor_kit:
            self.motor_kit.motor1.throttle = 0
            self.motor_kit.motor2.throttle = 0
            
    @property
    def left_arm_position(self) -> float:
        """Return the last set left arm position (0 to 1)."""
        with self._lock:
            return self._left_arm_position

    @property
    def right_arm_position(self) -> float:
        """Return the last set right arm position (0 to 1)."""
        with self._lock:
            return self._right_arm_position

    @property
    def head_pan(self) -> float:
        """Return the last set head pan angle."""
        with self._lock:
            return self._head_pan

    @property
    def head_tilt(self) -> float:
        """Return the last set head tilt angle."""
        with self._lock:
            return self._head_tilt

    def set_speeds(self, left: float, right: float):
        """Alias for set_motor_speeds."""
        return self.set_motor_speeds(left, right)

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
