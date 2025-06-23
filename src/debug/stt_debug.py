#!/usr/bin/env python3
"""
Standalone debug script for SpeechToTextModule.
Allows you to test phrase segmentation, dB thresholding, and transcription without running the full robot or API.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from modules.audio import AudioModule
from modules.speech_to_text import SpeechToTextModule
import logging
logger = logging.getLogger(__name__)

def on_transcription(text):
    print(f"[DEBUG SCRIPT] Transcription: {text}")

def on_timeout():
    logger.info("[DEBUG SCRIPT] Silence timeout reached.")

def main():
    logger.info("[DEBUG SCRIPT] Initializing audio...")
    audio = AudioModule(debug=True)
    logger.info("[DEBUG SCRIPT] Initializing SpeechToTextModule...")
    stt = SpeechToTextModule(audio_module=audio, debug=True)
    stt._audio_threshold = -40  # dB threshold for speech detection
    stt._phrase_timeout = 1.0   # Seconds of silence to trigger phrase segmentation
    stt.add_transcription_callback(on_transcription)
    stt.add_timeout_callback(on_timeout)
    logger.info("[DEBUG SCRIPT] Starting speech-to-text listening...")
    stt.start_listening()
    logger.info("[DEBUG SCRIPT] Speak into the microphone. Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        logger.warning("[DEBUG SCRIPT] Stopping...")
        stt.stop_listening()
        audio.cleanup()

if __name__ == "__main__":
    main()
