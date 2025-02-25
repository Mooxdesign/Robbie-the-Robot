#!/usr/bin/env python3

import os
import sys
import time
import numpy as np
import pyaudio
import threading
from typing import Optional

class AudioMonitor:
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.rate = 44100
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paFloat32
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        if status:
            print(f"Audio stream error: {status}")
            
        # Convert to numpy array
        data = np.frombuffer(in_data, dtype=np.float32)
        
        # Calculate volume (RMS)
        rms = np.sqrt(np.mean(np.square(data)))
        db = 20 * np.log10(rms) if rms > 0 else -100
        
        # Create visual meter
        meter_width = 50
        meter_level = int((db + 100) * meter_width / 100)
        meter = '█' * meter_level + '░' * (meter_width - meter_level)
        
        # Print the meter
        print(f"\rLevel: [{meter}] {db:>6.1f} dB", end='', flush=True)
        
        return (in_data, pyaudio.paContinue)
    
    def start(self):
        """Start monitoring audio levels"""
        if not self.stream:
            # List available devices
            print("\nAvailable audio devices:")
            for i in range(self.audio.get_device_count()):
                dev_info = self.audio.get_device_info_by_index(i)
                print(f"{i}: {dev_info['name']}")
            
            # Get device index from user
            dev_index = int(input("\nEnter device index (or press Enter for default): ") or -1)
            
            print("\nStarting audio monitor...")
            print("Press Ctrl+C to stop")
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=dev_index if dev_index >= 0 else None,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            self.is_running = True
            
            try:
                while self.stream.is_active():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopping audio monitor...")
                self.stop()
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.audio.terminate()

if __name__ == "__main__":
    monitor = AudioMonitor()
    monitor.start()