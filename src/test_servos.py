#!/usr/bin/env python3

import time
import logging
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from utils.hardware import MOTORS_AVAILABLE, SERVOS_AVAILABLE
from modules.motor import MotorModule

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_servos():
    """Test all servos by moving them through their full range"""
    
    print("=== Servo Test Script ===")
    print(f"Hardware detection - Motors: {MOTORS_AVAILABLE}, Servos: {SERVOS_AVAILABLE}")
    
    if not SERVOS_AVAILABLE:
        print("ERROR: Servos not detected. Check I2C connection and hardware.")
        return
    
    # Initialize motor module with debug enabled
    motors = MotorModule(debug=True)
    
    if not motors.servo_kit:
        print("ERROR: ServoKit failed to initialize")
        return
    
    print(f"ServoKit initialized successfully: {motors.servo_kit}")
    print(f"Number of servo channels: {motors.servo_kit.channels}")
    
    # Wait a moment for initialization
    time.sleep(1)
    
    # Test each servo
    servos_to_test = [
        (0, "Head Pan", -90, 90),      # Head pan servo
        (1, "Head Tilt", -45, 45),     # Head tilt servo  
        (2, "Left Arm", 0, 180),       # Left arm servo
        (3, "Right Arm", 0, 180),      # Right arm servo
    ]
    
    try:
        for channel, name, min_angle, max_angle in servos_to_test:
            print(f"\n--- Testing Servo {channel}: {name} ---")
            print(f"Range: {min_angle}° to {max_angle}°")
            
            # Move to center
            center_angle = (min_angle + max_angle) / 2
            print(f"Moving to center: {center_angle}°")
            
            if channel == 0:  # Head pan
                motors.move_head(pan=center_angle, tilt=None)
            elif channel == 1:  # Head tilt
                motors.move_head(pan=None, tilt=center_angle)
            elif channel == 2:  # Left arm
                pos = (center_angle - 0) / 180  # Convert angle to 0-1 position
                motors.move_arm('left', pos)
            elif channel == 3:  # Right arm
                pos = (center_angle - 0) / 180  # Convert angle to 0-1 position
                motors.move_arm('right', pos)
            
            time.sleep(2)
            
            # Move to minimum
            print(f"Moving to minimum: {min_angle}°")
            if channel == 0:
                motors.move_head(pan=min_angle, tilt=None)
            elif channel == 1:
                motors.move_head(pan=None, tilt=min_angle)
            elif channel == 2:
                pos = (min_angle - 0) / 180
                motors.move_arm('left', pos)
            elif channel == 3:
                pos = (min_angle - 0) / 180
                motors.move_arm('right', pos)
            
            time.sleep(2)
            
            # Move to maximum
            print(f"Moving to maximum: {max_angle}°")
            if channel == 0:
                motors.move_head(pan=max_angle, tilt=None)
            elif channel == 1:
                motors.move_head(pan=None, tilt=max_angle)
            elif channel == 2:
                pos = (max_angle - 0) / 180
                motors.move_arm('left', pos)
            elif channel == 3:
                pos = (max_angle - 0) / 180
                motors.move_arm('right', pos)
            
            time.sleep(2)
            
            # Return to center
            print(f"Returning to center: {center_angle}°")
            if channel == 0:
                motors.move_head(pan=center_angle, tilt=None)
            elif channel == 1:
                motors.move_head(pan=None, tilt=center_angle)
            elif channel == 2:
                pos = (center_angle - 0) / 180
                motors.move_arm('left', pos)
            elif channel == 3:
                pos = (center_angle - 0) / 180
                motors.move_arm('right', pos)
            
            time.sleep(2)
            
            print(f"✓ Servo {channel} ({name}) test complete")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"ERROR during servo test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return all servos to center position
        print("\n--- Returning all servos to center ---")
        try:
            motors.move_head(pan=0, tilt=0)  # Center head
            motors.move_arm('left', 0.5)     # Center left arm
            motors.move_arm('right', 0.5)    # Center right arm
            time.sleep(1)
        except Exception as e:
            print(f"ERROR returning servos to center: {e}")
        
        # Cleanup
        motors.cleanup()
        print("Servo test complete")

if __name__ == "__main__":
    test_servos()
