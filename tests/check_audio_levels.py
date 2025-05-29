#!/usr/bin/env python3

import os
import sys
import time

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.audio import AudioModule

def find_mic_index():
    """Find a working microphone"""
    import pyaudio
    p = pyaudio.PyAudio()
    
    print("\nSearching for microphones...")
    print("\nAvailable Input Devices:")
    
    # List all input devices
    input_devices = []
    for i in range(p.get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                input_devices.append((i, dev_info))
                print(f"{i}: {dev_info['name']}")
                print(f"   Max Inputs: {dev_info['maxInputChannels']}")
                print(f"   Default Sample Rate: {int(dev_info['defaultSampleRate'])} Hz")
        except:
            continue
            
    if not input_devices:
        p.terminate()
        return None
        
    # Try to find Amazon Basics mic first
    for idx, dev_info in input_devices:
        if 'AmazonBasics' in dev_info['name']:
            print(f"\nFound AmazonBasics microphone at index {idx}")
            p.terminate()
            return idx
            
    # Otherwise use first working mic
    idx, dev_info = input_devices[0]
    print(f"\nUsing first available microphone at index {idx}")
    p.terminate()
    return idx

def test_audio_monitor():
    """Test basic audio monitoring"""
    # Find working microphone
    mic_index = find_mic_index()
    if mic_index is None:
        print("Error: No working microphone found!")
        return
        
    # Create audio controller
    controller = AudioModule(device_index=mic_index, debug=True)
    
    try:
        # Enable meter display
        controller.enable_meter(True)
        
        # Start monitoring
        controller.start_stream()
        
        print("\nMonitoring audio levels. Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        controller.cleanup()

def test_audio_recording():
    """Test audio recording with monitoring"""
    # Find working microphone
    mic_index = find_mic_index()
    if mic_index is None:
        print("Error: No working microphone found!")
        return
        
    # Create audio controller
    controller = AudioModule(device_index=mic_index, debug=True)
    
    try:
        # Enable meter display
        controller.enable_meter(True)
        
        # Start stream and recording
        controller.start_stream()
        
        print("\nRecording will start in 3 seconds...")
        time.sleep(3)
        
        print("Recording started! Speak into the microphone.")
        print("Recording will stop after 5 seconds...")
        
        controller.start_recording()
        time.sleep(5)
        
        print("\nStopping recording...")
        controller.stop_recording()
        
        # Get recorded data
        print("\nProcessing recorded audio...")
        while True:
            data = controller.get_audio_data()
            if data is None:
                break
            # Could process the audio data here
            
        print("Done!")
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        controller.cleanup()

def test_volume_callback():
    """Test volume level callbacks"""
    def on_loud_sound(db_level):
        if db_level > -30:  # Threshold for speech
            print("\nLoud sound detected!")
    
    # Find working microphone
    mic_index = find_mic_index()
    if mic_index is None:
        print("Error: No working microphone found!")
        return
        
    # Create audio controller
    controller = AudioModule(device_index=mic_index, debug=True)
    
    try:
        # Add volume callback
        controller.add_volume_callback(on_loud_sound)
        
        # Start monitoring
        controller.start_stream()
        
        print("\nMonitoring for loud sounds. Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        controller.cleanup()

if __name__ == '__main__':
    print("Audio Controller Tests")
    print("=====================")
    print("1. Test audio monitoring")
    print("2. Test audio recording")
    print("3. Test volume callbacks")
    
    try:
        choice = input("\nEnter test number (1-3): ")
        
        if choice == '1':
            test_audio_monitor()
        elif choice == '2':
            test_audio_recording()
        elif choice == '3':
            test_volume_callback()
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\nTests cancelled.")
