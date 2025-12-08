#!/usr/bin/env python3
"""
Test script to verify head control modes configuration
"""

import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from src.controller.drive_controller import DriveController

def test_config():
    """Test configuration loading"""
    print("Testing head control configuration...")
    
    config = Config()
    
    # Test default values
    mode = config.get('joystick', 'head_control', 'mode', default='absolute')
    velocity_speed = config.get('joystick', 'head_control', 'velocity_speed', default=90.0)
    
    print(f"Head control mode: {mode}")
    print(f"Velocity speed: {velocity_speed} degrees/second")
    
    # Test servo configuration
    pan_config = {
        'channel': config.get('motor', 'servos', 'head_pan', 'channel', default=0),
        'min_angle': config.get('motor', 'servos', 'head_pan', 'min_angle', default=-90),
        'max_angle': config.get('motor', 'servos', 'head_pan', 'max_angle', default=90),
    }
    
    tilt_config = {
        'channel': config.get('motor', 'servos', 'head_tilt', 'channel', default=1),
        'min_angle': config.get('motor', 'servos', 'head_tilt', 'min_angle', default=-45),
        'max_angle': config.get('motor', 'servos', 'head_tilt', 'max_angle', default=45),
    }
    
    print(f"Pan servo config: {pan_config}")
    print(f"Tilt servo config: {tilt_config}")

def test_controller_modes():
    """Test DriveController with different modes"""
    print("\nTesting DriveController modes...")
    
    # Mock motors class for testing
    class MockMotors:
        def __init__(self):
            self.head_pan = 0.0
            self.head_tilt = 0.0
            
        def move_head(self, pan=None, tilt=None):
            if pan is not None:
                self.head_pan = pan
            if tilt is not None:
                self.head_tilt = tilt
            print(f"Mock head move: pan={pan}, tilt={tilt}")
            
        def snapshot(self):
            return {
                'head_pan': self.head_pan,
                'head_tilt': self.head_tilt
            }
            
        def stop(self):
            pass
    
    mock_motors = MockMotors()
    
    # Test absolute mode
    print("\n--- Testing Absolute Mode ---")
    controller = DriveController(mock_motors, debug=True)
    print(f"Controller mode: {controller._head_control_mode}")
    print(f"Controller velocity speed: {controller._head_velocity_speed}")
    
    # Simulate joystick input
    axes = [0, 0, 0, 0, 0, 0]  # [left_x, left_y, right_trigger, left_trigger, right_x, right_y]
    buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    # Test pan movement
    axes[3] = 0.5  # Right thumbstick half to the right
    controller.on_joystick_update(axes, buttons)
    
    axes[3] = -0.5  # Right thumbstick half to the left
    controller.on_joystick_update(axes, buttons)
    
    print("\n--- Testing Velocity Mode (config change) ---")
    # Temporarily modify config for testing
    config = Config()
    config._config['joystick']['head_control']['mode'] = 'velocity'
    
    controller2 = DriveController(mock_motors, debug=True)
    print(f"Controller mode: {controller2._head_control_mode}")
    
    # Test velocity movement
    axes[3] = 1.0  # Full right
    controller2.on_joystick_update(axes, buttons)
    
    import time
    time.sleep(0.1)  # Small delay to simulate time passing
    
    axes[3] = 0.0  # Center - should stop moving
    controller2.on_joystick_update(axes, buttons)
    
    axes[3] = -1.0  # Full left
    controller2.on_joystick_update(axes, buttons)

if __name__ == "__main__":
    test_config()
    test_controller_modes()
    print("\nTest completed!")
