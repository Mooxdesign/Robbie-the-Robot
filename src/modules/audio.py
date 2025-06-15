#!/usr/bin/env python3

import os
import sys
import time
import queue
import numpy as np
import pyaudio
import threading
from typing import Optional, Callable, List, Dict, Tuple

from config import Config

import wave

class AudioModule:
    """Core audio module for managing audio devices, streams, and routing"""
    
    # Common audio formats
    FORMAT_FLOAT32 = pyaudio.paFloat32
    FORMAT_INT16 = pyaudio.paInt16
    
    def __init__(self, device_index: Optional[int] = None, debug: bool = False):
        self._audio_level_callbacks: List[Callable[[float], None]] = []
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
        self.default_format = self.FORMAT_INT16  # Use int16 for compatibility
        
        # Audio state
        self._pyaudio = None
        self._streams: Dict[str, Dict] = {}  # Store active streams by ID
        
        # Initialize PyAudio
        self._initialize_pyaudio()

        # Debug: List and show selected audio input device
        if self.debug and self._pyaudio:
            print("\n[AudioModule] Listing available audio input devices:")
            for i in range(self._pyaudio.get_device_count()):
                try:
                    dev_info = self._pyaudio.get_device_info_by_index(i)
                    if dev_info.get('maxInputChannels', 0) > 0:
                        print(f"  [{i}] {dev_info['name']} (inputs: {dev_info.get('maxInputChannels', 0)})")
                except Exception as e:
                    print(f"  Error getting device {i} info: {e}")
            try:
                device_info = self._pyaudio.get_device_info_by_index(self.device_index) if self.device_index is not None else self._pyaudio.get_default_input_device_info()
                print(f"\n[AudioModule] Using audio input device: {device_info['name']} (index: {device_info['index']})")
                print(f"  [AudioModule] Device default sample rate: {device_info['defaultSampleRate']} Hz")
            except Exception as e:
                print(f"[AudioModule] Error getting selected device info: {e}")

    def add_audio_level_callback(self, callback: Callable[[float], None]) -> None:
        """Register a callback for real-time audio level (dB)."""
        self._audio_level_callbacks.append(callback)

    def _trigger_audio_level_callbacks(self, audio_level: float) -> None:
        """Trigger all registered audio level callbacks with the given dB level."""
        for callback in self._audio_level_callbacks:
            try:
                callback(audio_level)
            except Exception as e:
                if self.debug:
                    print(f"Error in audio level callback: {e}")
        
    def _initialize_pyaudio(self):
        try:
            self._pyaudio = pyaudio.PyAudio()
            if self.debug:
                print("PyAudio initialized successfully")
        except Exception as e:
            print(f"Failed to initialize PyAudio: {e}")
            
    def list_devices(self):
        """List available audio devices"""
        if not self._pyaudio:
            return
            
        print("\nAvailable audio devices:")
        for i in range(self._pyaudio.get_device_count()):
            try:
                dev_info = self._pyaudio.get_device_info_by_index(i)
                print(f"{i}: {dev_info['name']} (inputs: {dev_info.get('maxInputChannels', 0)})")
            except Exception as e:
                print(f"Error getting device {i} info: {e}")
        print()
        
    def get_device_info(self):
        """Get info about current audio device"""
        if not self._pyaudio:
            return None
            
        try:
            device_info = self._pyaudio.get_device_info_by_index(self.device_index) if self.device_index is not None else self._pyaudio.get_default_input_device_info()
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
        if not self._pyaudio:
            raise RuntimeError("Audio system not initialized")
            
        # Use defaults if not specified
        rate = rate or self.default_rate
        channels = channels or self.default_channels
        format = format or self.default_format  # Should be FORMAT_INT16 for input
        chunk_size = chunk_size or self.default_chunk_size
        
        def audio_callback(audio_data, frame_count, time_info, status):
            callback(audio_data, frame_count, time_info, status)
            # Convert bytes to numpy array (assuming 16-bit audio)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            # Calculate audio level in dB
            if len(audio_np) > 0:
                rms = np.sqrt(np.mean(audio_np ** 2))
                db = 20 * np.log10(rms + 1e-10)  # add epsilon to avoid log(0)
                # if self.debug:
                    # print(f"\rAudio ddevel: {db:.1f} dB", end="")
            return (None, pyaudio.paContinue)
        
        # Create stream
        stream_id = f"{rate}_{channels}_{format}_{chunk_size}_{input}_{output}"
        stream = self._pyaudio.open(format=format,
                               channels=channels,
                               rate=rate,
                               input=input,
                               output=output,
                               frames_per_buffer=chunk_size,
                               stream_callback=audio_callback)
        print(f"[AudioModule] Created stream with rate={rate}, channels={channels}, format={format}, chunk_size={chunk_size}")
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
        Pause an audio stream (can be resumed with start_stream).
        Args:
            stream_id: ID of stream to pause
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
        stream = self._streams[stream_id]["stream"]
        try:
            stream.stop_stream()
        except Exception as e:
            if self.debug:
                print(f"Error stopping stream: {e}")

    def close_stream(self, stream_id: str):
        """
        Stop (if needed) and close an audio stream, permanently releasing resources.
        Args:
            stream_id: ID of stream to close
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
        stream = self._streams[stream_id]["stream"]
        # Stop if not already stopped
        try:
            if stream.is_active():
                stream.stop_stream()
        except Exception:
            pass
        try:
            stream.close()
        except Exception as e:
            if self.debug:
                print(f"Error closing stream: {e}")
        finally:
            del self._streams[stream_id]

        
    def get_volume(self, signal: np.ndarray) -> float:
        """Compute RMS volume of an audio signal."""
        if not isinstance(signal, np.ndarray):
            raise ValueError("Input signal must be a numpy array")
        rms = np.sqrt(np.mean(np.square(signal)))
        return float(rms)

    def get_frequency(self, signal: np.ndarray) -> float:
        """Estimate the dominant frequency of an audio signal using FFT."""
        if not isinstance(signal, np.ndarray):
            raise ValueError("Input signal must be a numpy array")
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal))
        idx = np.argmax(np.abs(fft))
        freq = abs(freqs[idx])
        return float(freq)

    def play_sound(self, filename: str) -> None:
        """Play a WAV sound file."""
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        with wave.open(filename, 'rb') as wf:
            stream = self._pyaudio.open(
                format=self._pyaudio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            stream.start_stream()
            data = wf.readframes(wf.getnframes())
            stream.write(data)
            stream.stop_stream()
            stream.close()

    def record(self, duration: float = 1.0) -> bytes:
        """Record audio for a given duration (seconds)."""
        if duration <= 0:
            raise ValueError("Duration must be positive")
        stream = self._pyaudio.open(
            format=self.FORMAT_INT16,
            channels=1,
            rate=self.default_rate,
            input=True,
            frames_per_buffer=self.default_chunk_size
        )
        frames = []
        num_frames = int(self.default_rate / self.default_chunk_size * duration)
        for _ in range(num_frames):
            data = stream.read(self.default_chunk_size)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        return b''.join(frames)

    def cleanup(self) -> None:
        """Clean up resources"""
        print("\nCleaning up audio resources...")
        for stream_id in list(self._streams.keys()):
            stream = self._streams[stream_id]["stream"]
            try:
                stream.stop_stream()
            except Exception:
                pass
            try:
                stream.close()
            except Exception as e:
                if self.debug:
                    print(f"Error closing stream {stream_id}: {e}")
            del self._streams[stream_id]
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
                print("PyAudio terminated")
            except Exception as e:
                print(f"Error terminating PyAudio: {e}")
            self._pyaudio = None
