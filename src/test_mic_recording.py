#!/usr/bin/env python3
"""
Simple test to verify microphone recording functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
import numpy as np
import wave
from modules.audio import AudioModule
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_microphone():
    """Test basic microphone recording"""
    logger.info("=== Microphone Test ===")
    
    # Initialize audio module
    audio = AudioModule(debug=True)
    
    # Try to find AB13X USB microphone
    ab13x_index = audio.find_audio_device_by_name("USB Audio Device")
    if ab13x_index is not None:
        logger.info(f"Found AB13X microphone at index: {ab13x_index}")
        device_index = ab13x_index
        device_info = audio._pyaudio.get_device_info_by_index(device_index)
    else:
        logger.warning("AB13X not found, using default input device")
        device_info = audio._pyaudio.get_default_input_device_info()
        device_index = device_info['index']
        logger.info(f"Using default device: {device_info['name']} (index: {device_index['index']})")
    
    # Test recording
    logger.info("Starting 5-second recording test...")
    logger.info("Speak into the microphone now!")
    
    try:
        sample_rate = 48000  # Force standard rate instead of device default
        # Open stream
        stream = audio._pyaudio.open(
            format=audio.FORMAT_INT16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        stream.start_stream()
        logger.info("Recording started...")
        
        frames = []
        start_time = time.time()
        last_log_time = start_time
        
        while time.time() - start_time < 5:  # Record for 5 seconds
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
            
            # Calculate and log audio level every second
            current_time = time.time()
            if current_time - last_log_time > 1:
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                rms = np.sqrt(np.mean(audio_data ** 2))
                db = 20 * np.log10(rms) if rms > 0 else -100
                logger.info(f"Audio level: {db:.1f} dB (rms: {rms:.6f})")
                last_log_time = current_time
        
        stream.stop_stream()
        stream.close()
        
        logger.info("Recording finished!")
        
        # Save recording to file
        output_file = "test_recording.wav"
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        logger.info(f"Recording saved to: {output_file}")
        logger.info(f"File size: {os.path.getsize(output_file)} bytes")
        
        # Analyze the recording
        logger.info("=== Analysis ===")
        all_data = b''.join(frames)
        audio_array = np.frombuffer(all_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        max_amplitude = np.max(np.abs(audio_array))
        avg_rms = np.sqrt(np.mean(audio_array ** 2))
        max_db = 20 * np.log10(max_amplitude) if max_amplitude > 0 else -100
        avg_db = 20 * np.log10(avg_rms) if avg_rms > 0 else -100
        
        logger.info(f"Max amplitude: {max_amplitude:.6f} ({max_db:.1f} dB)")
        logger.info(f"Average RMS: {avg_rms:.6f} ({avg_db:.1f} dB)")
        
        if max_db > -30:
            logger.info("✓ Good audio levels detected!")
        elif max_db > -50:
            logger.warning("⚠ Low audio levels - speak louder or check mic")
        else:
            logger.error("✗ Very low audio levels - mic may not be working")
            
    except Exception as e:
        logger.error(f"Recording test failed: {e}")
        logger.exception("Full traceback:")
    
    finally:
        audio.cleanup()

if __name__ == "__main__":
    test_microphone()