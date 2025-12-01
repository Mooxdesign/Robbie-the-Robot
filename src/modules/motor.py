#!/usr/bin/env python3

import sys
import os
import time
import threading
from typing import Optional, Dict, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from utils.hardware import MOTORS_AVAILABLE, SERVOS_AVAILABLE

if MOTORS_AVAILABLE or SERVOS_AVAILABLE:
    import board
    from adafruit_motorkit import MotorKit
    from adafruit_servokit import ServoKit
    logger.info("Motor/servo hardware detected")
else:
    logger.info("No motor/servo hardware detected - hardware control disabled")
    MotorKit = None  # type: ignore
    ServoKit = None  # type: ignore

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
        self.acceleration = config.get('motor', 'dc_motors', 'acceleration', default=1.0)
        self.update_rate = config.get('motor', 'dc_motors', 'update_rate', default=50)
        
        # Initialize hardware
        self.motor_kit = None
        self.servo_kit = None
        
        logger.info(f"Hardware detection - Motors: {MOTORS_AVAILABLE}, Servos: {SERVOS_AVAILABLE}")
        
        if MOTORS_AVAILABLE or SERVOS_AVAILABLE:
            # Try to initialize MotorKit (DC motors)
            try:
                self.motor_kit = MotorKit(i2c=board.I2C()) if MotorKit else None
                if self.debug:
                    logger.info("MotorKit initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MotorKit (motors): {e}")
                self.motor_kit = None
            # Try to initialize ServoKit (servos)
            try:
                self.servo_kit = ServoKit(channels=16) if ServoKit else None
                if self.debug:
                    logger.info("ServoKit initialized successfully")
                logger.info(f"ServoKit created: {self.servo_kit is not None}")
            except Exception as e:
                logger.warning(f"Failed to initialize ServoKit (servos): {e}. Servo control will be disabled.")
                self.servo_kit = None
        else:
            logger.info("No motor/servo hardware detected - hardware control disabled")
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
        logger.debug("Motor update loop started")
        logger.info(self.motor_kit)

        with self._lock:
            self.target_left = max(min(left, self.max_speed), -self.max_speed)
            self.target_right = max(min(right, self.max_speed), -self.max_speed)

            # If hardware is present, throttle updates happen in _update_loop.
            # When no hardware, update current speeds immediately so telemetry reflects targets.
            if not self.motor_kit:
                self.left_speed = self.target_left
                self.right_speed = self.target_right

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
            logger.warning("move_head called but servo_kit is None")
            return
            
        logger.info(f"move_head called with pan={pan}, tilt={tilt}")
        with self._lock:
            # Set pan servo (0)
            if pan is not None:
                # Convert to 0-180 range
                angle = (pan + 90)  # -90 -> 0, 90 -> 180
                logger.info(f"Setting pan servo[0] to angle {angle}")
                self.servo_kit.servo[0].angle = angle
                self._head_pan = pan
            # Set tilt servo (1)
            if tilt is not None:
                # Convert to 0-180 range, but limit to -45 to 45
                angle = (tilt + 45) * 2  # -45 -> 0, 45 -> 180
                logger.info(f"Setting tilt servo[1] to angle {angle}")
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
            logger.warning("move_arm called but servo_kit is None")
            return
            
        logger.debug(f"move_arm called with side={side}, position={position}")
        with self._lock:
            # Convert 0-1 to 0-180
            angle = position * 180
            
            if side.lower() == 'left':
                logger.debug(f"Setting left arm servo[2] to angle {angle}")
                self.servo_kit.servo[2].angle = angle
                self._left_arm_position = position
            else:
                logger.debug(f"Setting right arm servo[3] to angle {angle}")
                self.servo_kit.servo[3].angle = angle
                self._right_arm_position = position
        
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()
            
        # Stop motors (all four channels if available)
        if self.motor_kit:
            try:
                self.motor_kit.motor1.throttle = 0
                self.motor_kit.motor2.throttle = 0
                self.motor_kit.motor3.throttle = 0
                self.motor_kit.motor4.throttle = 0
            except Exception:
                pass
            
    def snapshot(self) -> dict:
        """Return a thread-safe snapshot of motor targets and current speeds."""
        with self._lock:
            return {
                'target_left': float(self.target_left),
                'target_right': float(self.target_right),
                'left_speed': float(self.left_speed),
                'right_speed': float(self.right_speed),
                'left_arm_position': float(self._left_arm_position),
                'right_arm_position': float(self._right_arm_position),
                'head_pan': float(self._head_pan) if self._head_pan is not None else None,
                'head_tilt': float(self._head_tilt) if self._head_tilt is not None else None,
            }

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
        logger.info("Motor update loop started")
        logger.info(self.motor_kit)
        while self.is_running:
            current_time = time.time()
            dt = current_time - last_update
            last_update = current_time

            # DEBUG: Log motor kit and speeds every loop
            logger.debug(f"[DEBUG] motor_kit={self.motor_kit}, left_speed={self.left_speed:.2f}, right_speed={self.right_speed:.2f}, target_left={self.target_left:.2f}, target_right={self.target_right:.2f}")

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
                    
                # Set motor speeds (mirror to 4 channels)
                if self.motor_kit:
                    try:
                        # logger.info(f"[MOTOR] (Fallback) Setting motor1={self.left_speed:.2f}, motor2={self.right_speed:.2f}")
                        self.motor_kit.motor1.throttle = self.left_speed
                        self.motor_kit.motor2.throttle = self.left_speed
                        self.motor_kit.motor3.throttle = self.right_speed
                        self.motor_kit.motor4.throttle = self.right_speed
                    except Exception:
                        logger.error("[MOTOR] Failed to set any motor throttle!")
                        pass
                    self._last_hw_left = self.left_speed
                    self._last_hw_right = self.right_speed
            # Sleep to maintain update rate
            time.sleep(1 / self.update_rate)
