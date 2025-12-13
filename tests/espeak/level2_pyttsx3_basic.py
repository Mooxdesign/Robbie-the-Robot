#!/usr/bin/env python3
"""
Level 2: Python pyttsx3 Testing
Purpose: Verify pyttsx3 can use espeak backend
"""

import pyttsx3
import time

print("=" * 50)
print("LEVEL 2: PYTTSX3 BASIC TESTS")
print("=" * 50)
print()

# Test 2.1: Basic pyttsx3 initialization
print("Test 2.1: Initializing pyttsx3 engine...")
try:
    engine = pyttsx3.init()
    print("✓ Engine initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize engine: {e}")
    exit(1)

# List available voices
voices = engine.getProperty('voices')
print(f"\n✓ Available voices ({len(voices)}):")
for voice in voices:
    print(f"  - {voice.id}")
    print(f"    Name: {voice.name}")
    print(f"    Languages: {voice.languages}")

# Test basic speech
print("\nTesting basic speech...")
print("You should hear: 'Hello, I am Robbie the Robot'")
engine.say("Hello, I am Robbie the Robot")
engine.runAndWait()
print("✓ Basic speech test completed")
print()

# Test 2.2: Test voice properties
print("Test 2.2: Testing voice properties...")

# Test rate
print("\nTesting speech rate...")
print("Setting rate to 140 wpm (slower)...")
engine.setProperty('rate', 140)
engine.say("Testing slower speech rate")
engine.runAndWait()
time.sleep(0.5)

print("Setting rate to 200 wpm (faster)...")
engine.setProperty('rate', 200)
engine.say("Testing faster speech rate")
engine.runAndWait()
time.sleep(0.5)
print("✓ Rate tests completed")

# Test volume
print("\nTesting volume...")
print("Setting volume to 0.5 (half)...")
engine.setProperty('volume', 0.5)
engine.say("Testing half volume")
engine.runAndWait()
time.sleep(0.5)

print("Setting volume to 1.0 (full)...")
engine.setProperty('volume', 1.0)
engine.say("Testing full volume")
engine.runAndWait()
time.sleep(0.5)
print("✓ Volume tests completed")

# Test different voices if available
if len(voices) > 1:
    print(f"\nTesting voice switching (found {len(voices)} voices)...")
    for i, voice in enumerate(voices[:3]):  # Test first 3 voices
        print(f"Testing voice {i+1}: {voice.name}")
        engine.setProperty('voice', voice.id)
        engine.say(f"This is voice number {i+1}")
        engine.runAndWait()
        time.sleep(0.5)
    print("✓ Voice switching tests completed")

print()
print("=" * 50)
print("LEVEL 2 TESTS COMPLETED SUCCESSFULLY")
print("=" * 50)
