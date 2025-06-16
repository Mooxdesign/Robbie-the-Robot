import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.audio import AudioModule
from modules.voice import VoiceModule
import time

def debug_output_audio_callback(db_level):
    print(f"[DEBUG] Output audio level: {db_level:.1f} dB")

if __name__ == "__main__":
    # Use the correct output_device_index for your system (e.g., 2 for Stereo Mix)
    audio = AudioModule(output_device_index=2, debug=True)
    audio.add_output_audio_level_callback(debug_output_audio_callback)
    voice = VoiceModule(debug=True)
    time.sleep(1)  # Let threads initialize
    print("Speaking with TTS. You should see dB levels update...")
    voice.say("Hello, this is a test of the output audio level callback.", blocking=True)
    print("Now monitoring system output. Play any sound to see dB levels...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting output audio monitor.")
