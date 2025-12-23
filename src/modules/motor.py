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
        """
        Initialize motor controller
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._left_arm_position = 0.0
        self._right_arm_position = 0.0
        self._head_pan = None
        self._head_tilt = None
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        
        # DC motor settings
        self.max_speed = config.get('motor', 'dc_motors', 'max_speed', default=1.0)
        self.acceleration = config.get('motor', 'dc_motors', 'acceleration', default=1.0)
        self.update_rate = config.get('motor', 'dc_motors', 'update_rate', default=500)
        
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
                
                # Store servo configurations for pulse width conversion
                if self.servo_kit:
                    self.servo_configs = config.get('motor', 'servos', default={})
                    for servo_name, servo_config in self.servo_configs.items():
                        channel = servo_config.get('channel')
                        min_pulse = servo_config.get('min_pulse')
                        max_pulse = servo_config.get('max_pulse')
                        if channel is not None and min_pulse is not None and max_pulse is not None:
                            try:
                                self.servo_kit.servo[channel].set_pulse_width_range(min_pulse, max_pulse)
                                logger.info(f"Configured {servo_name} (channel {channel}): pulse range {min_pulse}-{max_pulse}")
                            except Exception as e:
                                logger.warning(f"Failed to configure {servo_name}: {e}")
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
        
        # Start update thread
        self.is_running = True
        self.update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self.update_thread.start()
        
    def set_motor_speeds(self, left: float, right: float):
        """
        Set motor speeds
        
        Args:
            left: Left motor speed (-1 to 1)
            right: Right motor speed (-1 to 1)
        """
        with self._lock:
            self.left_speed = max(min(left, self.max_speed), -self.max_speed)
            self.right_speed = max(min(right, self.max_speed), -self.max_speed)

            # If no hardware, update is complete
            if not self.motor_kit:
                return

    def stop(self):
        """Stop all motors"""
        self.set_motor_speeds(0, 0)
        
    def _normalized_to_pulse(self, normalized: float, min_pulse: int, max_pulse: int, center_pulse: Optional[int] = None) -> int:
        """
        Convert normalized value (-1.0 to 1.0) to pulse width
        
        Args:
            normalized: Value from -1.0 to 1.0
            min_pulse: Minimum pulse width in microseconds
            max_pulse: Maximum pulse width in microseconds
            center_pulse: Optional center pulse width for asymmetric scaling. If None, uses midpoint.
            
        Returns:
            Pulse width in microseconds
        """
        normalized = max(-1.0, min(1.0, normalized))
        
        # If no center_pulse specified, use midpoint for symmetric scaling
        if center_pulse is None:
            center_pulse = (min_pulse + max_pulse) // 2
        
        if normalized < 0:
            # Scale from center to min
            return int(center_pulse + normalized * (center_pulse - min_pulse))
        else:
            # Scale from center to max
            return int(center_pulse + normalized * (max_pulse - center_pulse))
    
    def _pulse_to_angle(self, pulse: int, min_pulse: int, max_pulse: int) -> float:
        """
        Convert pulse width to servo angle (0-180)
        
        Args:
            pulse: Pulse width in microseconds
            min_pulse: Minimum pulse width
            max_pulse: Maximum pulse width
            
        Returns:
            Angle in degrees (0-180)
        """
        return 180.0 * (pulse - min_pulse) / (max_pulse - min_pulse)

    def move_head(self, pan: Optional[float] = None, tilt: Optional[float] = None):
        """
        Move head servos
        
        Args:
            pan: Normalized pan position (-1.0 to 1.0, where 0 is center)
            tilt: Normalized tilt position (-1.0 to 1.0, where 0 is center)
        """
        if not self.servo_kit:
            logger.warning("move_head called but servo_kit is None")
            return
            
        logger.info(f"move_head called with pan={pan}, tilt={tilt}")
        with self._lock:
            # Set pan servo
            if pan is not None:
                pan_config = self.servo_configs.get('head_pan', {})
                channel = pan_config.get('channel', 14)
                min_pulse = pan_config.get('min_pulse', 500)
                center_pulse = pan_config.get('center_pulse')  # Optional
                max_pulse = pan_config.get('max_pulse', 2500)
                
                pulse = self._normalized_to_pulse(pan, min_pulse, max_pulse, center_pulse)
                angle = self._pulse_to_angle(pulse, min_pulse, max_pulse)
                
                logger.info(f"Setting pan {pan} -> pulse {pulse}μs -> angle {angle:.1f}° on servo[{channel}]")
                self.servo_kit.servo[channel].angle = angle
                self._head_pan = pan
                
            # Set tilt servo
            if tilt is not None:
                tilt_config = self.servo_configs.get('head_tilt', {})
                channel = tilt_config.get('channel', 15)
                min_pulse = tilt_config.get('min_pulse', 500)
                center_pulse = tilt_config.get('center_pulse')  # Optional
                max_pulse = tilt_config.get('max_pulse', 2500)
                
                pulse = self._normalized_to_pulse(tilt, min_pulse, max_pulse, center_pulse)
                angle = self._pulse_to_angle(pulse, min_pulse, max_pulse)
                
                logger.info(f"Setting tilt {tilt} -> pulse {pulse}μs -> angle {angle:.1f}° on servo[{channel}]")
                self.servo_kit.servo[channel].angle = angle
                self._head_tilt = tilt
                
    def move_arm(self, side: str, position: float):
        """
        Move arm servo
        
        Args:
            side: 'left' or 'right'
            position: Position from 0 to 1 (maps to full servo range)
        """
        if not self.servo_kit:
            logger.warning("move_arm called but servo_kit is None")
            return
            
        logger.info(f"move_arm called with side={side}, position={position}")
        with self._lock:
            # Get servo config
            servo_name = f"{side.lower()}_arm"
            arm_config = self.servo_configs.get(servo_name, {})
            channel = arm_config.get('channel', 0 if side.lower() == 'left' else 1)
            min_pulse = arm_config.get('min_pulse', 500)
            max_pulse = arm_config.get('max_pulse', 2500)
            
            # Convert 0-1 position directly to pulse width
            position = max(0.0, min(1.0, position))
            pulse = int(min_pulse + position * (max_pulse - min_pulse))
            angle = self._pulse_to_angle(pulse, min_pulse, max_pulse)
            
            logger.info(f"Setting {side} arm position {position} -> pulse {pulse}μs -> angle {angle:.1f}° on servo[{channel}]")
            self.servo_kit.servo[channel].angle = angle
            
            if side.lower() == 'left':
                self._left_arm_position = position
            else:
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
        """Return a thread-safe snapshot of motor speeds."""
        with self._lock:
            return {
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
        if self.debug:
            logger.debug(f"Motor update loop started (motor_kit available: {self.motor_kit is not None})")
        while self.is_running:
            current_time = time.time()
            dt = current_time - last_update
            last_update = current_time

            # DEBUG: Log motor kit and speeds every loop
            logger.debug(f"[DEBUG] motor_kit={self.motor_kit}, left_speed={self.left_speed:.2f}, right_speed={self.right_speed:.2f}")

            with self._lock:
                if self.motor_kit:
                    try:
                        self.motor_kit.motor1.throttle = self.left_speed
                        self.motor_kit.motor2.throttle = self.left_speed
                        self.motor_kit.motor3.throttle = self.right_speed
                        self.motor_kit.motor4.throttle = self.right_speed
                    except Exception as e:
                        logger.error(f"[MOTOR] Failed to set motor throttle: {e}")
            # Sleep to maintain update rate
            time.sleep(1 / self.update_rate)
