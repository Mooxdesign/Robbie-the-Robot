#!/usr/bin/env python3

import os
import sys
import time
import queue
import numpy as np
import pyaudio
import threading
from typing import Optional, Callable, List, Dict, Tuple

from src.config import Config

class AudioModule:
    """Core audio module for managing audio devices, streams, and routing"""
    
    # Common audio formats
    FORMAT_FLOAT32 = pyaudio.paFloat32
    FORMAT_INT16 = pyaudio.paInt16
    
    def __init__(self, device_index: Optional[int] = None, debug: bool = False):
        """
        Initialize audio module
        
        Args:
            device_index: Index of audio input device to use
            debug: Enable debug output
        """
        self.debug = debug
        self.device_index = device_index
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.default_rate = config.get('audio', 'rate', default=44100)
        self.default_chunk_size = config.get('audio', 'chunk_size', default=1024)
        self.default_channels = config.get('audio', 'channels', default=1)
        self.default_format = self.FORMAT_FLOAT32
        
        # Audio state
        self._pa = None
        self._streams: Dict[str, Dict] = {}  # Store active streams by ID
        
        # Initialize PyAudio
        self._initialize_pyaudio()
        
    def _initialize_pyaudio(self):
        try:
            self._pa = pyaudio.PyAudio()
            if self.debug:
                print("PyAudio initialized successfully")
        except Exception as e:
            print(f"Failed to initialize PyAudio: {e}")
            
    def list_devices(self):
        """List available audio devices"""
        if not self._pa:
            return
            
        print("\nAvailable audio devices:")
        for i in range(self._pa.get_device_count()):
            try:
                dev_info = self._pa.get_device_info_by_index(i)
                print(f"{i}: {dev_info['name']} (inputs: {dev_info.get('maxInputChannels', 0)})")
            except Exception as e:
                print(f"Error getting device {i} info: {e}")
        print()
        
    def get_device_info(self):
        """Get info about current audio device"""
        if not self._pa:
            return None
            
        try:
            device_info = self._pa.get_device_info_by_index(self.device_index) if self.device_index is not None else self._pa.get_default_input_device_info()
            print(f"\nUsing audio input device:")
            print(f"  Name: {device_info['name']}")
            print(f"  Index: {device_info['index']}")
            print(f"  Sample Rate: {int(device_info['defaultSampleRate'])} Hz")
            print(f"  Max Input Channels: {device_info['maxInputChannels']}")
            print()
            return device_info
        except Exception as e:
            print(f"Error getting device info: {e}")
            return None
            
    def create_stream(self, 
                     callback: Callable[[np.ndarray], None],
                     rate: Optional[int] = None,
                     channels: Optional[int] = None,
                     format: Optional[int] = None,
                     chunk_size: Optional[int] = None,
                     input: bool = True,
                     output: bool = False) -> str:
        """
        Create a new audio stream with specified parameters
        
        Args:
            callback: Function to call with audio data
            rate: Sample rate (Hz)
            channels: Number of channels
            format: Audio format (e.g. FORMAT_FLOAT32)
            chunk_size: Frames per buffer
            input: Enable input
            output: Enable output
            
        Returns:
            Stream ID string
        """
        if not self._pa:
            raise RuntimeError("Audio system not initialized")
            
        # Use defaults if not specified
        rate = rate or self.default_rate
        channels = channels or self.default_channels
        format = format or self.default_format
        chunk_size = chunk_size or self.default_chunk_size
        
        # Create stream
        stream_id = f"{rate}_{channels}_{format}_{chunk_size}_{input}_{output}"
        stream = self._pa.open(format=format,
                               channels=channels,
                               rate=rate,
                               input=input,
                               output=output,
                               frames_per_buffer=chunk_size,
                               stream_callback=callback)
        
        # Store stream
        self._streams[stream_id] = {"stream": stream, "callback": callback}
        
        return stream_id
        
    def start_stream(self, stream_id: str):
        """
        Start an audio stream
        
        Args:
            stream_id: ID of stream to start
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
            
        stream = self._streams[stream_id]["stream"]
        stream.start_stream()
        
    def stop_stream(self, stream_id: str):
        """
        Stop an audio stream
        
        Args:
            stream_id: ID of stream to stop
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
            
        # Just close the stream directly
        self.close_stream(stream_id)
        
    def close_stream(self, stream_id: str):
        """
        Close an audio stream
        
        Args:
            stream_id: ID of stream to close
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
            
        stream = self._streams[stream_id]["stream"]
        
        # Force close without trying to stop
        try:
            stream.close()
        except Exception as e:
            if self.debug:
                print(f"Error closing stream: {e}")
        finally:
            del self._streams[stream_id]
        
    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up audio resources...")
        for stream_id in list(self._streams.keys()):
            self.close_stream(stream_id)
        if self._pa:
            try:
                self._pa.terminate()
                print("PyAudio terminated")
            except Exception as e:
                print(f"Error terminating PyAudio: {e}")
            self._pa = None
