#!/usr/bin/env python3

import time
import threading
import json
import logging
import numpy as np
from typing import Dict, Optional
from .motor import MotorModule

logger = logging.getLogger(__name__)

class CalibrationController:
    """
    Handles motor and servo calibration routines
    """
    
    def __init__(self, motor: MotorModule, debug: bool = False):
        """
        Initialize calibration controller
        
        Args:
            motor: Reference to motor controller
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        self.motor = motor
        
        # Default calibration values
        self.calibration = {
            'motors': {
                'left': {
                    'neutral_point': 0.0,
                    'max_speed': 1.0,
                    'min_speed': 0.1
                },
                'right': {
                    'neutral_point': 0.0,
                    'max_speed': 1.0,
                    'min_speed': 0.1
                }
            },
            'servos': {
                'head_pan': {
                    'center': self.motor.HEAD_PAN_CENTER,
                    'min': self.motor.HEAD_PAN_RIGHT,
                    'max': self.motor.HEAD_PAN_LEFT
                },
                'head_tilt': {
                    'center': self.motor.HEAD_TILT_CENTER,
                    'min': self.motor.HEAD_TILT_UP,
                    'max': self.motor.HEAD_TILT_DOWN
                },
                'arm_left': {
                    'down': self.motor.ARM_LEFT_DOWN,
                    'up': self.motor.ARM_LEFT_UP
                },
                'arm_right': {
                    'down': self.motor.ARM_RIGHT_DOWN,
                    'up': self.motor.ARM_RIGHT_UP
                }
            }
        }
        
    def load_calibration(self, filename: str = 'calibration.json'):
        """Load calibration from file"""
        try:
            with open(filename, 'r') as f:
                self.calibration = json.load(f)
            if self.debug:
                logger.info("Loaded calibration from file")
        except Exception as e:
            logger.exception(f"Failed to load calibration: {e}")
            
    def save_calibration(self, filename: str = 'calibration.json'):
        """Save calibration to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.calibration, f, indent=2)
            if self.debug:
                logger.info("Saved calibration to file")
        except Exception as e:
            logger.exception(f"Failed to save calibration: {e}")
            
    def calibrate_motors(self) -> Dict:
        """
        Calibrate DC motors
        
        Returns:
            Dictionary with calibration results
        """
        with self._lock:
            results = {'left': {}, 'right': {}}
            
            for motor in ['left', 'right']:
                # Find neutral point
                neutral = self._find_neutral_point(motor)
                results[motor]['neutral_point'] = neutral
                
                # Find minimum speed
                min_speed = self._find_minimum_speed(motor)
                results[motor]['min_speed'] = min_speed
                
                # Find maximum safe speed
                max_speed = self._find_maximum_speed(motor)
                results[motor]['max_speed'] = max_speed
                
            # Update calibration
            self.calibration['motors'] = results
            return results
            
    def calibrate_servos(self) -> Dict:
        """
        Calibrate servo positions
        
        Returns:
            Dictionary with calibration results
        """
        with self._lock:
            results = {}
            
            # Calibrate head pan
            logger.info("Calibrating head pan...")
            self.motor.move_head(pan=0)
            input("Press Enter when head is centered horizontally")
            results['head_pan'] = {
                'center': self.motor.servo_positions['head_pan']
            }
            
            self.motor.move_head(pan=-1)
            input("Press Enter when head is at full right position")
            results['head_pan']['min'] = self.motor.servo_positions['head_pan']
            
            self.motor.move_head(pan=1)
            input("Press Enter when head is at full left position")
            results['head_pan']['max'] = self.motor.servo_positions['head_pan']
            
            # Calibrate head tilt
            logger.info("Calibrating head tilt...")
            self.motor.move_head(tilt=0)
            input("Press Enter when head is centered vertically")
            results['head_tilt'] = {
                'center': self.motor.servo_positions['head_tilt']
            }
            
            self.motor.move_head(tilt=-1)
            input("Press Enter when head is at full up position")
            results['head_tilt']['min'] = self.motor.servo_positions['head_tilt']
            
            self.motor.move_head(tilt=1)
            input("Press Enter when head is at full down position")
            results['head_tilt']['max'] = self.motor.servo_positions['head_tilt']
            
            # Calibrate arms
            logger.info("Calibrating left arm...")
            self.motor.move_arm('left', 0)
            input("Press Enter when left arm is in down position")
            results['arm_left'] = {
                'down': self.motor.servo_positions['arm_left']
            }
            
            self.motor.move_arm('left', 1)
            input("Press Enter when left arm is in up position")
            results['arm_left']['up'] = self.motor.servo_positions['arm_left']
            
            logger.info("Calibrating right arm...")
            self.motor.move_arm('right', 0)
            input("Press Enter when right arm is in down position")
            results['arm_right'] = {
                'down': self.motor.servo_positions['arm_right']
            }
            
            self.motor.move_arm('right', 1)
            input("Press Enter when right arm is in up position")
            results['arm_right']['up'] = self.motor.servo_positions['arm_right']
            
            # Update calibration
            self.calibration['servos'] = results
            return results
            
    def _find_neutral_point(self, motor: str) -> float:
        """Find motor neutral point (minimum voltage to overcome static friction)"""
        for voltage in np.linspace(0, 0.3, 30):
            if motor == 'left':
                self.motor.set_motor_speeds(voltage, 0)
            else:
                self.motor.set_motor_speeds(0, voltage)
            time.sleep(0.1)
            
            # TODO: Add movement detection using encoders or sensors
            # For now, return a reasonable default
            return 0.1
            
    def _find_minimum_speed(self, motor: str) -> float:
        """Find minimum speed for reliable movement"""
        # Start from neutral point
        neutral = self.calibration['motors'][motor]['neutral_point']
        
        for speed in np.linspace(neutral, 0.5, 20):
            if motor == 'left':
                self.motor.set_motor_speeds(speed, 0)
            else:
                self.motor.set_motor_speeds(0, speed)
            time.sleep(0.1)
            
            # TODO: Add movement detection
            # For now, return a reasonable default
            return 0.2
            
    def _find_maximum_speed(self, motor: str) -> float:
        """Find maximum safe speed based on current draw"""
        for speed in np.linspace(0.5, 1.0, 20):
            if motor == 'left':
                self.motor.set_motor_speeds(speed, 0)
            else:
                self.motor.set_motor_speeds(0, speed)
            time.sleep(0.1)
            
            # TODO: Add current monitoring
            # For now, return a reasonable default
            return 0.8
            
    def apply_calibration(self):
        """Apply loaded calibration to motor controller"""
        if self.motor:
            # Apply motor calibration
            self.motor.min_speed = max(
                self.calibration['motors']['left']['min_speed'],
                self.calibration['motors']['right']['min_speed']
            )
            self.motor.max_speed = min(
                self.calibration['motors']['left']['max_speed'],
                self.calibration['motors']['right']['max_speed']
            )
            
            # Apply servo calibration
            servos = self.calibration['servos']
            self.motor.HEAD_PAN_CENTER = servos['head_pan']['center']
            self.motor.HEAD_PAN_RIGHT = servos['head_pan']['min']
            self.motor.HEAD_PAN_LEFT = servos['head_pan']['max']
            
            self.motor.HEAD_TILT_CENTER = servos['head_tilt']['center']
            self.motor.HEAD_TILT_UP = servos['head_tilt']['min']
            self.motor.HEAD_TILT_DOWN = servos['head_tilt']['max']
            
            self.motor.ARM_LEFT_DOWN = servos['arm_left']['down']
            self.motor.ARM_LEFT_UP = servos['arm_left']['up']
            
            self.motor.ARM_RIGHT_DOWN = servos['arm_right']['down']
            self.motor.ARM_RIGHT_UP = servos['arm_right']['up']
            
            if self.debug:
                logger.info("Applied calibration to motor controller")
