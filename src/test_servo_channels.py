#!/usr/bin/env python3

import time
import logging
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from utils.hardware import MOTORS_AVAILABLE, SERVOS_AVAILABLE

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_servo_channels():
    """Test each servo channel directly to identify wiring"""
    
    print("=== Direct Servo Channel Test ===")
    print(f"Hardware detection - Motors: {MOTORS_AVAILABLE}, Servos: {SERVOS_AVAILABLE}")
    
    if not SERVOS_AVAILABLE:
        print("ERROR: Servos not detected. Check I2C connection and hardware.")
        return
    
    # Try to initialize servo kit directly
    try:
        import board
        from adafruit_servokit import ServoKit
        
        servo_kit = ServoKit(channels=16)
        print(f"ServoKit initialized successfully: {servo_kit}")
        print(f"Number of servo channels: {servo_kit._channels}")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize ServoKit: {e}")
        return
    
    # Wait a moment for initialization
    time.sleep(1)
    
    print("\n--- Testing all servo channels (0-15) ---")
    print("Watch which physical servo moves for each channel number")
    print("Press Ctrl+C to stop at any time\n")
    
    # Test all channels 0-15
    channels_to_test = list(range(16))
    
    try:
        for channel in channels_to_test:  # Test all channels 0-15
            print(f"=== Testing Channel {channel} ===")
            
            # Very quick movement test
            print(f"Channel {channel}: Moving...")
            servo_kit.servo[channel].angle = 45
            time.sleep(0.1)
            servo_kit.servo[channel].angle = 135
            time.sleep(0.1)
            servo_kit.servo[channel].angle = 90
            time.sleep(0.1)
            
            print(f"✓ Channel {channel} test complete\n")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"ERROR during servo test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return all servos to center position
        print("--- Returning all servos to center (90°) ---")
        try:
            for channel in range(16):
                servo_kit.servo[channel].angle = 90
            time.sleep(1)
        except Exception as e:
            print(f"ERROR returning servos to center: {e}")
        
        print("Direct servo channel test complete")

if __name__ == "__main__":
    test_servo_channels()
