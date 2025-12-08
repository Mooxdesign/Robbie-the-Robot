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

def test_head_tilt_advanced():
    """Advanced head tilt test with reset and different approaches"""
    
    print("=== Advanced Head Tilt Test ===")
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
    
    print("\n--- Test 1: Basic Movement Test ---")
    try:
        print("Testing channel 15 with simple movements...")
        
        # Test basic movement
        for angle in [90, 45, 135, 90]:
            print(f"Setting servo[15] to {angle}°")
            servo_kit.servo[15].angle = angle
            time.sleep(2)
    
    except Exception as e:
        print(f"ERROR in basic test: {e}")
    
    print("\n--- Test 2: Servo Reset and Reinitialize ---")
    try:
        print("Resetting servo...")
        # Set to 0 then back to 90 to reset
        servo_kit.servo[15].angle = 0
        time.sleep(1)
        servo_kit.servo[15].angle = 90
        time.sleep(2)
        
        print("Testing small movements...")
        for angle in [80, 100, 90]:
            print(f"Setting servo[15] to {angle}°")
            servo_kit.servo[15].angle = angle
            time.sleep(2)
    
    except Exception as e:
        print(f"ERROR in reset test: {e}")
    
    print("\n--- Test 3: Test Different Servo Channels ---")
    try:
        print("Testing if other channels work to rule out servo driver issue...")
        
        # Test channels 0, 1, 14 to see if they work
        test_channels = [0, 1, 14]
        for channel in test_channels:
            print(f"Testing servo[{channel}]...")
            servo_kit.servo[channel].angle = 90
            time.sleep(1)
            servo_kit.servo[channel].angle = 45
            time.sleep(1)
            servo_kit.servo[channel].angle = 90
            time.sleep(1)
            print(f"Channel {channel} test complete")
    
    except Exception as e:
        print(f"ERROR in channel test: {e}")
    
    print("\n--- Test 4: Pulse Width Test ---")
    try:
        print("Testing direct pulse width control...")
        # Try setting pulse width directly instead of angle
        servo = servo_kit.servo[15]
        
        # Test different pulse widths (500-2500 microseconds typical range)
        pulse_tests = [
            (1500, "Center pulse (1500μs)"),
            (1100, "Up pulse (1100μs)"),
            (1900, "Down pulse (1900μs)"),
            (1500, "Back to center (1500μs)"),
        ]
        
        for pulse, desc in pulse_tests:
            print(f"Setting pulse width to {pulse}μs - {desc}")
            # Set pulse width directly if supported
            try:
                servo.set_pulse_width_range(500, 2500)
                # Some servo kits support direct pulse setting
                if hasattr(servo, 'pulse_width'):
                    servo.pulse_width = pulse
                else:
                    # Fallback to angle calculation
                    angle = ((pulse - 500) / 2000) * 180
                    servo.angle = angle
                time.sleep(2)
            except Exception as e:
                print(f"Pulse width setting failed: {e}")
    
    except Exception as e:
        print(f"ERROR in pulse test: {e}")
    
    print("\n--- Test 5: Physical Inspection Test ---")
    print("Please check the following:")
    print("1. Is the servo physically connected to channel 15?")
    print("2. Can the servo move freely (not mechanically blocked)?")
    print("3. Is the servo receiving power (LED on, warm to touch)?")
    print("4. Are the servo wires secure (signal, power, ground)?")
    
    input("Press Enter when ready to continue...")
    
    print("\n--- Final Test: Return to Center ---")
    try:
        print("Returning all servos to center position...")
        for channel in [0, 1, 14, 15]:
            servo_kit.servo[channel].angle = 90
        time.sleep(1)
        print("All servos returned to center")
    
    except Exception as e:
        print(f"ERROR in final test: {e}")
    
    print("\nAdvanced head tilt test complete")

if __name__ == "__main__":
    test_head_tilt_advanced()
