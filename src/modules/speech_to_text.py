#!/usr/bin/env python3

import threading
import queue
import numpy as np
import whisper
from typing import Optional, Callable, Dict, List
import time

from src.modules.audio import AudioModule

class SpeechToTextModule:
    """Speech-to-text conversion using Whisper"""
    
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    MIN_AUDIO_CHUNKS = 10
    
    def __init__(self, 
                 audio_module: Optional[AudioModule] = None,
                 language: str = "en-US",
                 debug: bool = False):
        """
        Initialize speech-to-text module
        
        Args:
            audio_module: AudioModule instance to use for audio handling. If None, creates new instance
            language: Language code for speech recognition
            debug: Enable debug output
        """
        self.debug = debug
        self.language = language
        self._lock = threading.Lock()
        
        # Use provided audio module or create new one
        self.audio = audio_module if audio_module else AudioModule(debug=debug)
        
        # Initialize Whisper
        try:
            self.whisper = whisper.load_model("base")
            if self.debug:
                print("Whisper model loaded")
        except Exception as e:
            print(f"Failed to initialize Whisper: {e}")
            self.whisper = None
            return
            
        # Speech processing setup
        self.is_listening = False
        self._audio_buffer = []
        self._last_audio = time.time()
        self._process_thread = None
        self._transcription_callbacks: List[Callable[[str], None]] = []
        self._timeout_callbacks: List[Callable[[], None]] = []
        self._silence_timeout = 5.0  # Seconds of silence before timeout
        self._audio_threshold = -42  # dB threshold for speech detection
        
    def add_transcription_callback(self, callback: Callable[[str], None]):
        """Add callback for transcribed text"""
        self._transcription_callbacks.append(callback)
        
    def add_timeout_callback(self, callback: Callable[[], None]):
        """Add callback for silence timeout"""
        self._timeout_callbacks.append(callback)
        
    def start_listening(self):
        """Start listening and converting speech to text"""
        if self.is_listening:
            if self.debug:
                print("Cannot start speech recognition: already listening")
            return
            
        # Reset state
        if hasattr(self, '_stream_id'):
            try:
                self.audio.close_stream(self._stream_id)
            except Exception as e:
                if self.debug:
                    print(f"Error closing existing stream: {e}")
            del self._stream_id
            
        # Stop any existing processing thread
        if self._process_thread and self._process_thread.is_alive():
            if self.debug:
                print("Waiting for processing thread to finish")
            self._process_thread.join(timeout=1)
            
        self.is_listening = True
        self._audio_buffer = []
        self._last_audio = time.time()
        self._process_thread = None
        
        try:
            # Start audio stream through AudioModule
            self._stream_id = self.audio.create_stream(
                callback=self._audio_callback,
                rate=self.SAMPLE_RATE,
                chunk_size=self.CHUNK_SIZE,
                format=AudioModule.FORMAT_FLOAT32,
                channels=1
            )
            if self.debug:
                print("Starting speech recognition")
            self.audio.start_stream(self._stream_id)
        except Exception as e:
            print(f"Failed to start speech recognition: {e}")
            self.is_listening = False
            if hasattr(self, '_stream_id'):
                del self._stream_id
                
    def stop_listening(self):
        """Stop listening for speech"""
        # Always try to clean up stream regardless of state
        if not self.is_listening and not hasattr(self, '_stream_id'):
            if self.debug:
                print("Cannot stop speech recognition: not listening")
            return
            
        self.is_listening = False
        
        # Process any remaining audio before stopping
        if self._audio_buffer and len(self._audio_buffer) >= self.MIN_AUDIO_CHUNKS:
            if self.debug:
                print("Processing remaining audio before stopping")
            self._process_audio()
            
        # Stop audio stream through AudioModule
        if hasattr(self, '_stream_id'):
            try:
                self.audio.close_stream(self._stream_id)
                if self.debug:
                    print("Closed speech recognition stream")
            except Exception as e:
                if self.debug:
                    print(f"Error stopping speech recognition stream: {e}")
            del self._stream_id
        
        # Clear state
        self._audio_buffer = []
        self._last_audio = 0
        
        if self._process_thread:
            self._process_thread.join(timeout=1)
            self._process_thread = None
            
    def _audio_callback(self, in_data, frame_count, time_info, status_flags):
        """
        Process audio data from stream
        
        Args:
            in_data: Raw audio data
            frame_count: Number of frames
            time_info: Dictionary with timing information
            status_flags: PyAudio status flags
            
        Returns:
            Tuple of (bytes, status flag) for PyAudio
        """
        if not self.is_listening:
            if self.debug:
                print("Audio callback called but not listening")
            return (None, 0)  # Continue
            
        try:
            # Convert raw bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Calculate audio level in dB
            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(audio_data**2))
                db = 20 * np.log10(rms) if rms > 0 else -100
                
                # Only update last audio time if sound is above threshold
                if db > self._audio_threshold:
                    self._last_audio = time.time()
                    self._audio_buffer.append(audio_data)
                    
                if self.debug:
                    print(f"\rAudio Level: {db:.1f} dB", end="")
                    
                # Check for timeout
                elapsed = time.time() - self._last_audio
                if elapsed > self._silence_timeout:
                    # if self.debug:
                        # print("\nSilence timeout")
                    # Notify timeout callbacks
                    for callback in self._timeout_callbacks:
                        try:
                            callback()
                        except Exception as e:
                            if self.debug:
                                print(f"Error in timeout callback: {e}")
                    return (None, 0)
                    
                # If we have enough audio and no speech detected recently, process it
                if len(self._audio_buffer) >= self.MIN_AUDIO_CHUNKS and elapsed > 0.5:
                    if not self._process_thread or not self._process_thread.is_alive():
                        self._process_thread = threading.Thread(target=self._process_audio)
                        self._process_thread.start()
                    
        except Exception as e:
            if self.debug:
                print(f"\nError processing audio: {e}")
                
        return (None, 0)  # Continue

    def _process_audio(self):
        """Process collected audio data"""
        if not self.whisper:
            return
            
        try:
            # Check if we have enough audio
            if len(self._audio_buffer) < self.MIN_AUDIO_CHUNKS:
                return
                
            # Convert buffer to numpy array
            audio_data = np.concatenate(self._audio_buffer)
            
            # Transcribe
            if self.debug:
                print("\nTranscribing audio...")
                
            result = self.whisper.transcribe(audio_data)
            text = result["text"].strip()
            
            if text:
                # Notify callbacks in main thread
                if threading.current_thread() != threading.main_thread():
                    # Schedule callback in main thread
                    threading.Timer(0, self._notify_callbacks, args=[text]).start()
                else:
                    self._notify_callbacks(text)
                    
            # Clear buffer after processing
            self._audio_buffer = []
            
        except Exception as e:
            if self.debug:
                print(f"Error processing audio: {e}")
                
        finally:
            # Clear thread reference
            self._process_thread = None
            
    def _notify_callbacks(self, text: str):
        """Notify callbacks in main thread"""
        for callback in self._transcription_callbacks:
            try:
                callback(text)
            except Exception as e:
                if self.debug:
                    print(f"Error in transcription callback: {e}")
                    
    def cleanup(self):
        """Clean up resources"""
        # Stop listening if active
        if self.is_listening:
            self.stop_listening()
            
        # Clean up Whisper
        if self.whisper:
            del self.whisper
