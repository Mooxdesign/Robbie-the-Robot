#!/usr/bin/env python3
"""
Level 3: VoiceModule Integration Testing
Purpose: Test the robot's VoiceModule class
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from modules.voice import VoiceModule

print("=" * 50)
print("LEVEL 3: VOICEMODULE INTEGRATION TESTS")
print("=" * 50)
print()

# Test 3.1: VoiceModule initialization
print("Test 3.1: Initializing VoiceModule...")
try:
    voice = VoiceModule(rate=140, volume=1.0, debug=True)
    time.sleep(2)  # Let thread start and initialize
    print("✓ VoiceModule initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize VoiceModule: {e}")
    exit(1)

# Test basic speech
print("\nTesting VoiceModule.say() (non-blocking)...")
print("You should hear: 'Hello, I am Robbie the Robot'")
result = voice.say("Hello, I am Robbie the Robot")
if result:
    print("✓ say() returned True")
    time.sleep(4)  # Wait for speech to complete
else:
    print("✗ say() returned False")

# Test blocking speech
print("\nTesting blocking speech...")
print("You should hear: 'This is blocking speech'")
result = voice.say("This is blocking speech", blocking=True)
if result:
    print("✓ Blocking speech completed")
else:
    print("✗ Blocking speech failed")

# Test queue functionality
print("\nTesting speech queue (multiple items)...")
voice.say("First message")
voice.say("Second message")
voice.say("Third message", blocking=True)
print("✓ Queue test completed")

print()

# Test 3.2: VoiceModule voice selection
print("Test 3.2: Testing voice selection...")

# List available voices
voices = voice.get_voices()
print(f"✓ Found {len(voices)} voices:")
for vid, vinfo in list(voices.items())[:5]:  # Show first 5
    print(f"  - {vinfo['name']}")
    print(f"    Gender: {vinfo.get('gender', 'unknown')}")
    print(f"    Languages: {vinfo.get('languages', [])}")

# Test voice change if multiple voices available
if len(voices) > 1:
    print("\nTesting voice change...")
    voice_ids = list(voices.keys())
    
    # Try first voice
    first_voice_id = voice_ids[0]
    print(f"Changing to: {voices[first_voice_id]['name']}")
    if voice.change_voice(voice_id=first_voice_id):
        print("✓ Voice changed successfully")
        voice.say("Testing first voice", blocking=True)
    else:
        print("✗ Voice change failed")
    
    # Try second voice if available
    if len(voice_ids) > 1:
        second_voice_id = voice_ids[1]
        print(f"Changing to: {voices[second_voice_id]['name']}")
        if voice.change_voice(voice_id=second_voice_id):
            print("✓ Voice changed successfully")
            voice.say("Testing second voice", blocking=True)
        else:
            print("✗ Voice change failed")

# Test rate and volume changes
print("\nTesting rate changes...")
voice.set_rate(100)
voice.say("Very slow speech", blocking=True)
voice.set_rate(200)
voice.say("Very fast speech", blocking=True)
voice.set_rate(140)  # Reset to normal
print("✓ Rate change tests completed")

print("\nTesting volume changes...")
voice.set_volume(0.3)
voice.say("Quiet speech", blocking=True)
voice.set_volume(1.0)
voice.say("Loud speech", blocking=True)
print("✓ Volume change tests completed")

# Cleanup
print("\nCleaning up VoiceModule...")
voice.cleanup()
print("✓ VoiceModule cleanup completed")

print()
print("=" * 50)
print("LEVEL 3 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
