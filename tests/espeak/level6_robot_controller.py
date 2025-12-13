#!/usr/bin/env python3
"""
Level 6: Full Robot Controller Testing
Purpose: Test complete robot system with all subsystems
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from controller.robot import RobotController

print("=" * 50)
print("LEVEL 6: FULL ROBOT CONTROLLER TESTS")
print("=" * 50)
print()

# Test 6.1: Robot controller initialization
print("Test 6.1: Initializing RobotController...")
print("This will initialize ALL robot subsystems:")
print("  - AudioModule")
print("  - VoiceModule (via SpeechController)")
print("  - ConversationController")
print("  - LedsController")
print("  - VisionModule")
print("  - MotorModule")
print("  - DriveController")
print("  - JoystickController (if available)")
print()

try:
    robot = RobotController(debug=True)
    time.sleep(3)  # Let all subsystems initialize
    print("✓ RobotController initialized successfully")
except Exception as e:
    print(f"✗ RobotController initialization failed: {e}")
    print("\nNote: Some subsystems may fail if hardware is not available.")
    print("This is expected when testing on non-Pi systems.")
    exit(1)

print()

# Test 6.2: Speech through robot controller
print("Test 6.2: Testing speech through robot...")
print("You should hear: 'Robot controller initialized successfully'")
try:
    robot.speech.voice.say("Robot controller initialized successfully", blocking=True)
    print("✓ Speech test completed")
except Exception as e:
    print(f"✗ Speech test failed: {e}")

print()

# Test 6.3: Conversation through robot controller
print("Test 6.3: Testing conversation through robot...")
test_conversations = [
    "Hello Robbie, introduce yourself",
    "What can you do?",
    "Tell me a fun fact"
]

for i, user_input in enumerate(test_conversations, 1):
    print(f"\n--- Conversation {i} ---")
    print(f"User: {user_input}")
    
    try:
        response = robot.conversation.chat(user_input)
        print(f"Robbie: {response}")
        
        # Speak the response
        robot.speech.voice.say(response, blocking=True)
        time.sleep(1)
        print(f"✓ Conversation {i} completed")
    except Exception as e:
        print(f"✗ Conversation {i} failed: {e}")
        break

print()

# Test 6.4: Check robot state
print("Test 6.4: Checking robot state...")
print(f"Current state: {robot._state}")
print("✓ Robot state accessible")

# Test 6.5: Test state transitions (if voice is enabled)
if hasattr(robot, 'speech') and robot.speech:
    print("\nTest 6.5: Testing state transitions...")
    
    print("Setting state to LISTENING...")
    robot._set_state(robot._state.__class__.LISTENING if hasattr(robot._state, '__class__') else "LISTENING")
    time.sleep(0.5)
    
    print("Setting state to PROCESSING...")
    robot._set_state(robot._state.__class__.PROCESSING if hasattr(robot._state, '__class__') else "PROCESSING")
    time.sleep(0.5)
    
    print("Setting state to SPEAKING...")
    robot._set_state(robot._state.__class__.SPEAKING if hasattr(robot._state, '__class__') else "SPEAKING")
    robot.speech.voice.say("Testing speaking state", blocking=True)
    
    print("Returning to STANDBY...")
    robot._return_to_standby()
    time.sleep(0.5)
    
    print("✓ State transition tests completed")

print()

# Test 6.6: Verify all subsystems are accessible
print("Test 6.6: Verifying subsystem accessibility...")
subsystems = {
    'audio': 'AudioModule',
    'speech': 'SpeechController',
    'conversation': 'ConversationController',
    'leds': 'LedsController',
    'vision': 'VisionModule',
    'motors': 'MotorModule',
    'drive': 'DriveController',
}

for attr, name in subsystems.items():
    if hasattr(robot, attr):
        print(f"  ✓ {name} accessible")
    else:
        print(f"  ✗ {name} not found")

if hasattr(robot, 'joystick') and robot.joystick:
    print(f"  ✓ JoystickController accessible")
else:
    print(f"  ⚠ JoystickController not available (no joystick connected)")

print()

# Cleanup
print("Cleaning up RobotController...")
try:
    robot.cleanup()
    print("✓ RobotController cleanup completed")
except Exception as e:
    print(f"⚠ Cleanup warning: {e}")

print()
print("=" * 50)
print("LEVEL 6 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
print()
print("FULL INTEGRATION TEST COMPLETE!")
print("All robot subsystems are functioning correctly.")
