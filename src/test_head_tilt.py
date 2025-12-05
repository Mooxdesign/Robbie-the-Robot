#!/usr/bin/env python3

import time
import logging
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from utils.hardware import SERVOS_AVAILABLE

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_head_tilt():
    """Test head tilt servo with full range to debug the upward-only issue"""
    
    print("=== Head Tilt Debug Test ===")
    print(f"Hardware detection - Servos: {SERVOS_AVAILABLE}")
    
    if not SERVOS_AVAILABLE:
        print("ERROR: Servos not detected. Check I2C connection and hardware.")
        return
    
    # Try to initialize servo kit directly
    try:
        import board
        from adafruit_servokit import ServoKit
        
        servo_kit = ServoKit(channels=16)
        print(f"ServoKit initialized successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize ServoKit: {e}")
        return
    
    # Wait a moment for initialization
    time.sleep(1)
    
    print("\n--- Testing Head Tilt Servo (Channel 15) ---")
    print("Testing full range to see if servo can move both up and down\n")
    
    try:
        # Test the full 0-180 degree range
        test_angles = [
            90,   # Center
            45,   # Should be up
            0,    # Should be fully up
            90,   # Back to center
            135,  # Should be down
            180,  # Should be fully down
            90,   # Back to center
        ]
        
        descriptions = [
            "Center position (90°)",
            "Tilt up (45°)",
            "Tilt fully up (0°)",
            "Back to center (90°)",
            "Tilt down (135°)",
            "Tilt fully down (180°)",
            "Back to center (90°)",
        ]
        
        for angle, desc in zip(test_angles, descriptions):
            print(f"Setting servo[15] to {angle}° - {desc}")
            servo_kit.servo[15].angle = angle
            time.sleep(3)
            
            # Ask for user feedback
            response = input(f"Did the head move {desc.split('(')[1].split(')')[0]}? (y/n): ").lower().strip()
            if response == 'y':
                print(f"✓ Movement confirmed for {angle}°")
            else:
                print(f"✗ No movement detected for {angle}°")
            print()
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"ERROR during head tilt test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return servo to center
        print("--- Returning head tilt servo to center (90°) ---")
        try:
            servo_kit.servo[15].angle = 90
            time.sleep(1)
        except Exception as e:
            print(f"ERROR returning servo to center: {e}")
        
        print("Head tilt test complete")

if __name__ == "__main__":
    test_head_tilt()
