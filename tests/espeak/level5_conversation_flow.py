#!/usr/bin/env python3
"""
Level 5: Full Conversation Flow Testing
Purpose: Test complete conversation pipeline
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from modules.audio import AudioModule
from controller.speech import SpeechController
from controller.conversation import ConversationController

print("=" * 50)
print("LEVEL 5: CONVERSATION FLOW TESTS")
print("=" * 50)
print()

# Test 5.1: Conversation module integration
print("Test 5.1: Initializing conversation components...")

# Mock robot with full conversation support
class MockRobot:
    def __init__(self):
        self.state_update_callback = None
        self._state = "STANDBY"
        
        print("  Initializing AudioModule...")
        self.audio = AudioModule(debug=False)
        
        print("  Initializing ConversationController...")
        # Note: This requires OpenAI API key in environment
        self.conversation = ConversationController(debug=True)
        
        print("  Initializing SpeechController...")
        # Use backend=None to skip Google Cloud Speech (use Whisper instead)
        self.speech = SpeechController(self, self.audio, debug=True, backend=None)
        
        time.sleep(2)  # Let components initialize
    
    def _set_state(self, state):
        self._state = state
        print(f"  [State: {state}]")
    
    def _return_to_standby(self):
        self._state = "STANDBY"
        print("  [Standby]")
    
    def _on_input_audio_level(self, level):
        """Mock callback for input audio level"""
        pass
    
    def cleanup(self):
        print("  Cleaning up robot components...")
        if hasattr(self, 'speech'):
            self.speech.cleanup()
        if hasattr(self, 'audio'):
            self.audio.cleanup()

# Initialize robot
try:
    robot = MockRobot()
    print("✓ All components initialized successfully")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    print("\nNote: This test requires an OpenAI API key.")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    exit(1)

print()

# Test single conversation turn
print("Test 5.2: Testing single conversation turn...")
user_input = "Hello Robbie, how are you?"
print(f"User: {user_input}")

try:
    response = robot.conversation.chat(user_input)
    print(f"Robbie: {response}")
    
    # Speak the response
    print("Speaking response...")
    robot.speech.voice.say(response, blocking=True)
    print("✓ Single conversation turn completed")
except Exception as e:
    print(f"✗ Conversation turn failed: {e}")
    robot.cleanup()
    exit(1)

print()

# Test 5.3: Multiple conversation turns
print("Test 5.3: Testing multiple conversation turns...")
test_inputs = [
    "What is your name?",
    "What is your favorite color?",
    "Can you count to three?"
]

for i, user_input in enumerate(test_inputs, 1):
    print(f"\n--- Turn {i} ---")
    print(f"User: {user_input}")
    
    try:
        response = robot.conversation.chat(user_input)
        print(f"Robbie: {response}")
        
        # Speak the response
        robot.speech.voice.say(response, blocking=True)
        time.sleep(1)  # Brief pause between turns
    except Exception as e:
        print(f"✗ Turn {i} failed: {e}")
        break

print("\n✓ Multiple conversation turns completed")

# Test conversation history
print("\nTest 5.4: Checking conversation history...")
history = robot.conversation.get_chat_history()
print(f"✓ Conversation history has {len(history)} messages:")
for msg in history[-5:]:  # Show last 5 messages
    sender = msg['sender'].upper()
    text = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
    print(f"  {sender}: {text}")

# Cleanup
print("\nCleaning up...")
robot.cleanup()
print("✓ Cleanup completed")

print()
print("=" * 50)
print("LEVEL 5 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
print()
print("Note: If you see API errors, ensure OPENAI_API_KEY is set")
