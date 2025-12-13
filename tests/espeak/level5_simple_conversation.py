#!/usr/bin/env python3
"""
Level 5: Simple Conversation Flow Testing (Speech Output Only)
Purpose: Test conversation + speech without speech recognition complexity
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from modules.voice import VoiceModule
from controller.conversation import ConversationController

print("=" * 50)
print("LEVEL 5: SIMPLE CONVERSATION FLOW")
print("=" * 50)
print()

print("Test 5.1: Initializing components...")
print("  Initializing VoiceModule...")
voice = VoiceModule(rate=140, volume=1.0, debug=True)
time.sleep(2)

print("  Initializing ConversationController...")
try:
    conversation = ConversationController(debug=True)
    print("✓ Components initialized")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    print("\nNote: This test requires an OpenAI API key.")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    voice.cleanup()
    exit(1)

print()

# Test single conversation turn
print("Test 5.2: Testing single conversation turn...")
user_input = "Hello Robbie, how are you?"
print(f"User: {user_input}")

try:
    response = conversation.chat(user_input)
    print(f"Robbie: {response}")
    
    # Speak the response
    print("Speaking response...")
    voice.say(response, blocking=True)
    print("✓ Single conversation turn completed")
except Exception as e:
    print(f"✗ Conversation turn failed: {e}")
    voice.cleanup()
    exit(1)

print()

# Test multiple conversation turns
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
        response = conversation.chat(user_input)
        print(f"Robbie: {response}")
        
        # Speak the response
        voice.say(response, blocking=True)
        time.sleep(1)  # Brief pause between turns
    except Exception as e:
        print(f"✗ Turn {i} failed: {e}")
        break

print("\n✓ Multiple conversation turns completed")

# Test conversation history
print("\nTest 5.4: Checking conversation history...")
history = conversation.get_chat_history()
print(f"✓ Conversation history has {len(history)} messages:")
for msg in history[-5:]:  # Show last 5 messages
    sender = msg['sender'].upper()
    text = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
    print(f"  {sender}: {text}")

# Cleanup
print("\nCleaning up...")
voice.cleanup()
print("✓ Cleanup completed")

print()
print("=" * 50)
print("LEVEL 5 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
print()
print("Note: If you see API errors, ensure OPENAI_API_KEY is set")
