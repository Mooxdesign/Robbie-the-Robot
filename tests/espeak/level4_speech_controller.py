#!/usr/bin/env python3
"""
Level 4: SpeechController Integration Testing
Purpose: Test text-to-speech through SpeechController
"""

import sys
import time
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from modules.audio import AudioModule
from controller.speech import SpeechController

print("=" * 50)
print("LEVEL 4: SPEECHCONTROLLER INTEGRATION TESTS")
print("=" * 50)
print()

# Test 4.1: SpeechController initialization
print("Test 4.1: Initializing SpeechController...")

# Mock parent object (minimal RobotController interface)
class MockRobot:
    def __init__(self):
        self.state_update_callback = None
        self.conversation = None
        self._state = "STANDBY"
    
    def _set_state(self, state):
        self._state = state
        print(f"  [State changed to: {state}]")
    
    def _return_to_standby(self):
        self._state = "STANDBY"
        print("  [Returning to standby]")
    
    def _on_input_audio_level(self, level):
        """Mock callback for input audio level"""
        pass

# Initialize components
print("Initializing AudioModule...")
try:
    audio = AudioModule(debug=False)
    print("✓ AudioModule initialized")
except Exception as e:
    print(f"✗ AudioModule initialization failed: {e}")
    exit(1)

print("Initializing MockRobot...")
mock_robot = MockRobot()
print("✓ MockRobot initialized")

print("Initializing SpeechController...")
try:
    speech = SpeechController(mock_robot, audio, debug=True)
    time.sleep(2)  # Let components initialize
    print("✓ SpeechController initialized")
except Exception as e:
    print(f"✗ SpeechController initialization failed: {e}")
    audio.cleanup()
    exit(1)

# Test speech output through SpeechController
print("\nTest 4.2: Testing speech output...")
print("You should hear: 'Hello from Speech Controller'")
try:
    speech.voice.say("Hello from Speech Controller", blocking=True)
    print("✓ Speech output successful")
except Exception as e:
    print(f"✗ Speech output failed: {e}")

# Test multiple speech commands
print("\nTest 4.3: Testing multiple speech commands...")
test_phrases = [
    "Testing speech controller",
    "This is the second phrase",
    "And this is the third phrase"
]

for i, phrase in enumerate(test_phrases, 1):
    print(f"Speaking phrase {i}: '{phrase}'")
    speech.voice.say(phrase, blocking=True)
    time.sleep(0.5)
print("✓ Multiple speech commands completed")

# Test voice properties through SpeechController
print("\nTest 4.4: Testing voice properties...")
print("Testing rate change...")
speech.voice.set_rate(100)
speech.voice.say("Slow speech", blocking=True)
speech.voice.set_rate(180)
speech.voice.say("Fast speech", blocking=True)
speech.voice.set_rate(140)  # Reset
print("✓ Rate change test completed")

print("Testing volume change...")
speech.voice.set_volume(0.5)
speech.voice.say("Half volume", blocking=True)
speech.voice.set_volume(1.0)
speech.voice.say("Full volume", blocking=True)
print("✓ Volume change test completed")

# Cleanup
print("\nCleaning up...")
try:
    speech.cleanup()
    print("✓ SpeechController cleanup completed")
except Exception as e:
    print(f"⚠ SpeechController cleanup warning: {e}")

try:
    audio.cleanup()
    print("✓ AudioModule cleanup completed")
except Exception as e:
    print(f"⚠ AudioModule cleanup warning: {e}")

print()
print("=" * 50)
print("LEVEL 4 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
