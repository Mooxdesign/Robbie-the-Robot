#!/usr/bin/env python3

from modules.voice import VoiceModule
import signal
import sys

def signal_handler(sig, frame):
    print('\nCleaning up...')
    if 'voice' in globals():
        voice.cleanup()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize voice module with debug output
    voice = VoiceModule(debug=True)
    
    # Test speaking
    print("\nTesting speech with default voice:")
    voice.say("Testing the voice module with George's voice.", blocking=True)
    
    # Clean up
    voice.cleanup()

if __name__ == "__main__":
    main()