#!/usr/bin/env python3

import threading
import numpy as np
try:
    import pvporcupine
except ImportError:
    # Dummy pvporcupine for test context
    class DummyPorcupine:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    pvporcupine = DummyPorcupine()
import time
from typing import Optional, Callable, List

from .audio import AudioModule

import logging
logger = logging.getLogger(__name__)

class WakeWordInitError(Exception):
    """Raised when the wake word module fails to initialize properly."""
    pass

class WakeWordModule:
    """
    Wake word detection using Porcupine.

    Public Properties:
        has_active_stream (bool): True if an audio stream is currently active, False otherwise.
    """
    
    def __init__(self, 
                 audio_module: Optional[AudioModule] = None,
                 wake_word: str = "porcupine",
                 sensitivity: float = 0.5,
                 access_key: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize wake word detector
        
        Args:
            audio_module: AudioModule instance for audio handling
            wake_word: Wake word to listen for
            sensitivity: Detection sensitivity (0-1)
            access_key: Picovoice access key
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Use provided audio module or create new one
        self.audio = audio_module if audio_module else AudioModule(debug=debug)
        
        # Initialize Porcupine
        try:
            logger.debug(f"wake_word={wake_word}, access_key={access_key}")
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[wake_word] if wake_word.endswith('.ppn') else None,
                keywords=[wake_word] if not wake_word.endswith('.ppn') else None,
                sensitivities=[sensitivity]
            )
            if self.debug:
                logger.info("Porcupine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            raise WakeWordInitError(f"Porcupine initialization failed: {e}")

            
        # Detection setup
        self.is_listening = False
        self._stream_id = None
        self._detection_callbacks: List[Callable[[], None]] = []

    @property
    def has_active_stream(self) -> bool:
        """
        Returns True if an audio stream is currently active, False otherwise.
        """
        return self._stream_id is not None
        
    def add_detection_callback(self, callback: Callable[[], None]):
        """Add callback for wake word detection"""
        self._detection_callbacks.append(callback)
        
    def start_listening(self):
        """Start listening for wake word"""
        if self.is_listening or not self.porcupine:
            if self.debug:
                logger.warning(f"Cannot start wake word: already listening={self.is_listening}, porcupine={self.porcupine is not None}")
            return
            
        self.is_listening = True
        
        try:
            # Start audio stream through AudioModule
            self._stream_id = self.audio.create_stream(
                callback=self._audio_callback,
                rate=self.porcupine.sample_rate,
                chunk_size=self.porcupine.frame_length,
                format=AudioModule.FORMAT_INT16,  # Porcupine requires 16-bit integers
                channels=1
            )
            if self.debug:
                logger.info("Starting wake word detection")
            self.audio.start_stream(self._stream_id)
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            self.is_listening = False
            
    def stop_listening(self):
        """Stop listening for wake word"""
        if not self.is_listening:
            return
            
        self.is_listening = False
        if self.debug:
            logger.info("Stopped wake word detection")
        
        if self._stream_id:
            try:
                self.audio.close_stream(self._stream_id)
            except Exception as e:
                if self.debug:
                    logger.error(f"Error stopping wake word stream: {e}")
            self._stream_id = None
            
    def _audio_callback(self, in_data, frame_count, time_info, status_flags):
        """
        Process audio data for wake word detection
        
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
                logger.warning("Wake word callback called but not listening")
            return (None, 0)  # Continue
            
        try:
            # Convert raw bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            # Process with Porcupine
            result = self.porcupine.process(audio_data)
            
            if result >= 0:  # Wake word detected
                if self.debug:
                    logger.info("Wake word detected!")
                    
                # Notify callbacks
                for callback in self._detection_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        if self.debug:
                            logger.error(f"Error in detection callback: {e}")
                    
        except Exception as e:
            if self.debug:
                logger.error(f"Error processing audio: {e}")
                
        return (None, 0)  # Continue

    def cleanup(self):
        """Clean up resources"""
        # Stop listening if active
        if self.is_listening:
            self.stop_listening()
            
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
