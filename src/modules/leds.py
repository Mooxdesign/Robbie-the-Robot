#!/usr/bin/env python3

import sys
import os
import time
import threading
import colorsys
import numpy as np
from typing import Tuple, List, Optional

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from utils.hardware import LED_AVAILABLE

import logging
logger = logging.getLogger(__name__)

if LED_AVAILABLE:
    import unicornhat as unicorn
    logger.info("Unicorn pHAT detected")
class LedsModule:
    """
    Handles direct interaction with the LED hardware (Unicorn HAT Mini),
    buffer management, and thread safety. All higher-level control and pattern logic
    should be handled by LedsController and LedsAnimations.
    """
    # All visualization and pattern logic has been moved to LedsController and LedsAnimations.
    # This class now only provides hardware and buffer access methods.
    """
    Controls the Unicorn pHAT LED matrix with various patterns and animations
    """
    
    def __init__(self, brightness: float = 0.5, debug: bool = False):
        self.current_color = (0, 0, 0)
        """
        Initialize LED module
        
        Args:
            brightness: LED brightness (0.0 to 1.0)
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        self.width = Config().get('lights', 'width', default=8)
        self.height = Config().get('lights', 'height', default=4)
        
        # Initialize LED hardware
        try:
            self.unicorn = unicorn
            self.unicorn.set_layout(self.unicorn.PHAT)
            self.unicorn.brightness(brightness)
            if self.debug:
                logger.info("LED matrix initialized (pHAT)")
        except Exception as e:
            logger.error(f"Failed to initialize LED matrix: {e}")
            self.unicorn = None
            
        # Pattern buffers
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)  # (rows, cols, rgb)
        
        # Audio visualization state
        self.max_volume = float('-inf')
        self.min_volume = float('inf')
        self.volume_decay = 0.05  # How quickly volume range adapts
        self.volume_smoothing = 0.3  # Smoothing factor for volume changes
        self.last_volume = 0

        # Callback hooks
        self._update_callbacks = []
        
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set color of a single pixel"""
        with self._lock:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y, x] = [r, g, b]
                if self.unicorn:
                    self.unicorn.set_pixel(x, y, r, g, b)
    
    def set_all(self, r: int, g: int, b: int):
        """Set all pixels to the same color"""
        self.requested_color = (r, g, b)
        brightness = self.unicorn.get_brightness() if hasattr(self, 'unicorn') and self.unicorn and hasattr(self.unicorn, 'get_brightness') else 1.0
        scaled = (round(r * brightness), round(g * brightness), round(b * brightness))
        self.current_color = scaled
        with self._lock:
            self.buffer = np.full((self.height, self.width, 3), [r, g, b], dtype=np.uint8)
            if self.unicorn:
                for y in range(self.height):
                    for x in range(self.width):
                        self.unicorn.set_pixel(x, y, *scaled)
    
    def clear(self):
        """Turn off all pixels"""
        self.set_all(0, 0, 0)
        self.show()
    
    def show(self):
        """Update the display with current buffer"""
        if self.unicorn:
            self.unicorn.show()
        # Trigger update callbacks
        for callback in self._update_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in LED update callback: {e}")
    
    # Rainbow animation logic has been moved to LedsAnimations.
    
    # Pulse animation logic has been moved to LedsAnimations.
    
    # Wave animation logic has been moved to LedsAnimations.
    
    # Sparkle animation logic has been moved to LedsAnimations.
    
    def add_update_callback(self, callback):
        """Register a callback to be triggered on LED updates."""
        self._update_callbacks.append(callback)
    
    def visualize_audio(self, volume: float, color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Visualize audio volume on LED matrix
        
        Args:
            volume: Current audio volume level
            color: RGB color tuple for visualization
        """
        with self._lock:
            # Update volume range with decay
            self.max_volume = max(volume, self.max_volume * (1 - self.volume_decay))
            self.min_volume = min(volume, self.min_volume * (1 + self.volume_decay))
            
            # Normalize volume
            if self.max_volume == self.min_volume:
                normalized = 0
            else:
                normalized = (volume - self.min_volume) / (self.max_volume - self.min_volume)
                
            # Smooth changes
            normalized = (normalized * (1 - self.volume_smoothing) + 
                        self.last_volume * self.volume_smoothing)
            self.last_volume = normalized
            
            # Scale to full range and add minimum brightness
            brightness = 0.1 + 0.9 * normalized
            
            # Set LED colors
            r, g, b = [int(c * brightness) for c in color]
            self.set_all(r, g, b)
            self.show()
            
    def start_audio_visualization(self, color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Start continuous audio visualization
        
        Args:
            color: RGB color tuple for visualization
        """
        import pyaudio
        import numpy as np
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 22050
        
        def audio_callback(in_data, frame_count, time_info, status):
            # Calculate volume from audio data
            data = np.frombuffer(in_data, dtype=np.int16)
            volume = np.abs(data).mean()
            self.visualize_audio(volume, color)
            return (in_data, pyaudio.paContinue)
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback
        )
        
        # Start stream
        stream.start_stream()
        
        return stream, p
        
    def stop_audio_visualization(self, stream, p):
        """Stop audio visualization and cleanup"""
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        p.terminate()
        self.clear()
    
    def visualize_audio(self, audio_data: np.ndarray, threshold: float = 0.1):
        """
        Visualize audio data on the LED matrix
        
        Args:
            audio_data: Numpy array of audio samples
            threshold: Minimum amplitude to trigger visualization
        """
        if len(audio_data) == 0:
            return
            
        # Normalize audio data
        audio_data = np.abs(audio_data)
        max_amp = np.max(audio_data)
        if max_amp > threshold:
            # Scale to LED height
            scaled = (audio_data / max_amp * self.height).astype(int)
            
            # Clear display
            self.clear()
            
            # Draw visualization
            for x in range(min(self.width, len(scaled))):
                height = min(scaled[x], self.height)
                for y in range(height):
                    # Color gradient from blue to red
                    hue = (y / self.height) * 0.7  # Hue range for blue-red
                    rgb = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    self.set_pixel(x, y, *rgb)
            
            self.show()
    
    # Pulse and rainbow animation logic has been refactored out of this module.

    def set_brightness(self, value: float):
        """Set the brightness of the LED matrix."""
        if hasattr(self, 'unicorn') and self.unicorn:
            try:
                self.unicorn.set_brightness(value)
                if hasattr(self, 'requested_color'):
                    r, g, b = self.requested_color
                    self.set_color(r, g, b)
                if self.debug:
                    logger.info(f"LED brightness set to {value}")
            except Exception as e:
                if self.debug:
                    logger.error(f"Failed to set brightness: {e}")

    def set_color(self, r: int, g: int, b: int):
        """Set all LEDs to the specified color (with validation)."""
        for val in (r, g, b):
            if not (0 <= val <= 255):
                raise ValueError("Color values must be between 0 and 255")
        self.set_all(r, g, b)

    def cleanup(self):
        """Clean up resources and turn off LEDs"""
        self.clear()
        if self.debug:
            logger.info("LED cleanup completed")
