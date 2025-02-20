#!/usr/bin/env python3

import os
import sys
import time
import threading
import queue
import numpy as np
import pyaudio
from typing import Optional, Callable, List

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import Config

class AudioController:
    """Audio input and output controller"""
    
    def __init__(self, debug: bool = False):
        """
        Initialize audio controller
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.rate = config.get('audio', 'rate', default=44100)
        self.chunk_size = config.get('audio', 'chunk_size', default=1024)
        self.channels = config.get('audio', 'channels', default=1)
        self.format = pyaudio.paFloat32
        
        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
            if self.debug:
                print("Audio initialized")
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            self.audio = None
            
        # Audio state
        self.stream = None
        self.is_recording = False
        self.recording_thread = None
        self.audio_queue = queue.Queue()
        self.volume_callbacks = []
        
    def start_stream(self, callback: Optional[Callable[[np.ndarray], None]] = None):
        """
        Start audio input stream
        
        Args:
            callback: Optional callback for audio data
        """
        if not self.audio:
            return
            
        with self._lock:
            if not self.stream:
                try:
                    def audio_callback(in_data, frame_count, time_info, status):
                        if status:
                            print(f"Audio stream error: {status}")
                            
                        # Convert to numpy array
                        data = np.frombuffer(in_data, dtype=np.float32)
                        
                        # Calculate volume
                        volume = np.abs(data).mean()
                        
                        # Call volume callbacks
                        for cb in self.volume_callbacks:
                            try:
                                cb(volume)
                            except Exception as e:
                                print(f"Error in volume callback: {e}")
                                
                        # Call data callback if provided
                        if callback:
                            try:
                                callback(data)
                            except Exception as e:
                                print(f"Error in audio callback: {e}")
                                
                        return (in_data, pyaudio.paContinue)
                        
                    self.stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        output=False,
                        frames_per_buffer=self.chunk_size,
                        stream_callback=audio_callback
                    )
                    
                    self.stream.start_stream()
                    
                    if self.debug:
                        print("Audio stream started")
                        
                except Exception as e:
                    print(f"Failed to start audio stream: {e}")
                    self.stream = None
                    
    def stop_stream(self):
        """Stop audio input stream"""
        with self._lock:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                
                if self.debug:
                    print("Audio stream stopped")
                    
    def start_recording(self):
        """Start recording audio to queue"""
        if not self.audio:
            return
            
        with self._lock:
            if not self.is_recording:
                self.is_recording = True
                self.recording_thread = threading.Thread(
                    target=self._record_audio,
                    daemon=True
                )
                self.recording_thread.start()
                
    def stop_recording(self):
        """Stop recording audio"""
        with self._lock:
            self.is_recording = False
            
        if self.recording_thread:
            self.recording_thread.join()
            self.recording_thread = None
            
    def get_audio(self) -> Optional[np.ndarray]:
        """Get recorded audio data"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
            
    def add_volume_callback(self, callback: Callable[[float], None]):
        """Add callback for audio volume"""
        self.volume_callbacks.append(callback)
        
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        self.stop_stream()
        
        if self.audio:
            self.audio.terminate()
            
    def _record_audio(self):
        """Record audio to queue"""
        if not self.audio:
            return
            
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        while self.is_recording:
            try:
                data = stream.read(self.chunk_size)
                audio_data = np.frombuffer(data, dtype=np.float32)
                self.audio_queue.put(audio_data)
            except Exception as e:
                print(f"Error recording audio: {e}")
                break
                
        stream.stop_stream()
        stream.close()

    def play_sound(self, sound_name: str):
        """
        Play a predefined sound
        
        Args:
            sound_name: Name of the sound to play
        """
        # In simulation mode, just log the sound
        print(f"[SIM] Playing sound: {sound_name}")
