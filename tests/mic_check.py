#!/usr/bin/env python3

import os
import sys
import time
import speech_recognition as sr
import unittest
import numpy as np

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.voice import VoiceModule
from src.modules.audio import AudioModule

def list_microphones():
    """List all available microphones"""
    print("\nAvailable Microphones:")
    mic = sr.Microphone()
    for i, mic_name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{i}: {mic_name}")
    print()

def find_usb_mic_index():
    """Find the AmazonBasics USB mic index"""
    # Try to find the first full name match
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        if "AmazonBasics Portable USB Mic" in name:
            return i
            
    # Fall back to partial match
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        if "AmazonBasics" in name:
            return i
            
    return None

def test_voice_recognition():
    """Test voice recognition"""
    print("Testing voice recognition...")
    
    # Find USB mic
    mic_index = find_usb_mic_index()
    if mic_index is None:
        print("Could not find AmazonBasics USB microphone!")
        return
        
    print(f"\nUsing AmazonBasics USB microphone (index {mic_index})")
    voice = VoiceModule(debug=True, device_index=mic_index)
    
    print("\nContinuous Voice Recognition Test")
    print("================================")
    print("1. First I'll calibrate the microphone")
    print("2. Then I'll start listening")
    print("3. Speak normally - I'll show what I hear")
    print("4. Press Enter when you want to stop")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    # Use a queue for thread communication
    import queue
    command_queue = queue.Queue()
    
    def listen_thread():
        while True:
            try:
                # Check if we should stop
                try:
                    # Non-blocking check for stop command
                    if command_queue.get_nowait() == "stop":
                        break
                except queue.Empty:
                    pass
                    
                # Listen without timeout
                text = voice.listen(timeout=None)
                if text:
                    print(f"\nHeard: {text}")
            except Exception as e:
                print(f"Error in listen thread: {e}")
                break
    
    # Start listening thread
    import threading
    listen_thread = threading.Thread(target=listen_thread, daemon=True)
    listen_thread.start()
    
    print("\nListening... Press Enter to stop")
    input()  # Wait for Enter
    
    # Signal thread to stop
    command_queue.put("stop")
    listen_thread.join(timeout=2)  # Wait for thread to finish
    
    print("\nStopped listening. Test complete!")
    
import numpy as np

def test_audio_levels():
    """Test audio input levels (mocked for environments without audio hardware)"""
    print("Testing audio input levels...")

    # Patch PyAudio and stream
    with patch("pyaudio.PyAudio") as MockPyAudio:
        mock_pa = MockPyAudio.return_value
        mock_stream = MagicMock()
        mock_pa.open.return_value = mock_stream
        mock_pa.get_device_count.return_value = 1
        mock_pa.get_device_info_by_index.return_value = {"name": "Fake Mic", "maxInputChannels": 1, "index": 0, "defaultSampleRate": 44100}

        audio = AudioModule(debug=True)

        # Callback to print volume levels
        def print_volume(volume):
            bars = int(volume * 50)  # Scale volume to 0-50 range
            print(f"Volume: {'#' * bars}{' ' * (50 - bars)} [{volume:.3f}]", end='\r')

        audio.add_volume_callback(print_volume)

        print("\nStarting audio stream...")
        # Create a stream with a callback that computes volume and triggers the callbacks
        def audio_callback(data):
            # Simulate a random volume between 0 and 1
            fake_data = np.random.rand(1024).astype(np.float32)
            volume = audio.get_volume(fake_data)
            for cb in audio._audio_level_callbacks:
                cb(volume)

        stream_id = audio.create_stream(callback=audio_callback)
        audio.start_stream(stream_id)

        print("Recording for 5 seconds. (Simulated audio input)")
        for _ in range(10):
            audio_callback(None)
            time.sleep(0.5)

        audio.stop_stream(stream_id)
        print("\nDone testing audio levels")

if __name__ == "__main__":
    print("=== Testing Microphone Input ===")
    
    print("\nChecking available microphones...")
    list_microphones()
    
    print("\n1. Testing voice recognition")
    test_voice_recognition()
    
    print("\n2. Testing audio input levels")
    test_audio_levels()
    
    print("\nTests complete!")
