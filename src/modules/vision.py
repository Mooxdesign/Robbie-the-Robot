#!/usr/bin/env python3

import sys
import os
import time
import cv2
import threading
import numpy as np
from typing import List, Dict, Optional, Tuple
from queue import Queue

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from utils.hardware import CAMERA_AVAILABLE

if CAMERA_AVAILABLE:
    from picamera2 import Picamera2
    print("Camera detected - using hardware camera")
else:
    print("No camera detected - running in simulation mode")

class VideoStream:
    """
    Camera object that controls video streaming from the Picamera
    Runs in separate thread for better performance
    """
    
    def __init__(self, 
                 resolution: Tuple[int, int] = (640, 480),
                 framerate: int = 30):
        """
        Initialize video stream
        
        Args:
            resolution: Camera resolution (width, height)
            framerate: Target framerate
        """
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_preview_configuration(
            main={"format": 'XRGB8888', "size": resolution}
        ))
        self.cam.start()
        
        # Get initial frame
        self.frame = self.cam.capture_array()
        self.stopped = False
        self.thread = None
        
    def start(self):
        """Start the video stream thread"""
        self.thread = threading.Thread(
            target=self._update,
            daemon=True
        )
        self.thread.start()
        return self
        
    def _update(self):
        """Update loop for video stream"""
        while not self.stopped:
            self.frame = self.cam.capture_array()
            
    def read(self) -> np.ndarray:
        """Get the most recent frame"""
        return self.frame
        
    def stop(self):
        """Stop the video stream thread"""
        self.stopped = True
        if self.thread:
            self.thread.join()
        self.cam.stop()

class VisionModule:
    """Vision processing module"""
    
    def __init__(self, debug: bool = False):
        """
        Initialize vision module
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.width = config.get('vision', 'camera', 'width', default=640)
        self.height = config.get('vision', 'camera', 'height', default=480)
        self.framerate = config.get('vision', 'camera', 'framerate', default=30)
        
        # Initialize camera
        try:
            if CAMERA_AVAILABLE:
                self.camera = Picamera2()
                self.camera.configure(
                    self.camera.create_preview_configuration(
                        main={"size": (self.width, self.height)}
                    )
                )
            else:
                self.camera = cv2.VideoCapture(0)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
                
            if self.debug:
                print("Camera initialized")
                
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.camera = None
            
        # Vision processing state
        self.is_running = False
        self.processing_thread = None
        self.current_frame = None
        self.detected_objects = []
        self.callbacks = []
        
    def start(self):
        """Start vision processing"""
        if not self.camera:
            return
            
        with self._lock:
            if not self.is_running:
                self.is_running = True
                if CAMERA_AVAILABLE:
                    self.camera.start()
                self.processing_thread = threading.Thread(
                    target=self._process_frames,
                    daemon=True
                )
                self.processing_thread.start()
                
                if self.debug:
                    print("Vision processing started")
                    
    def stop(self):
        """Stop vision processing"""
        with self._lock:
            self.is_running = False
            
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None
            
        if self.camera:
            if CAMERA_AVAILABLE:
                self.camera.stop()
            else:
                self.camera.release()
                
        if self.debug:
            print("Vision processing stopped")
            
    def add_callback(self, callback):
        """Add callback for detected objects"""
        self.callbacks.append(callback)
        
    def get_frame(self):
        """Get current frame"""
        with self._lock:
            return self.current_frame.copy() if self.current_frame is not None else None
            
    def get_objects(self):
        """Get detected objects"""
        with self._lock:
            return self.detected_objects.copy()
            
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        
    def _process_frames(self):
        """Process camera frames"""
        while self.is_running:
            try:
                # Get frame
                if CAMERA_AVAILABLE:
                    frame = self.camera.capture_array()
                else:
                    ret, frame = self.camera.read()
                    if not ret:
                        continue
                        
                # Store frame
                with self._lock:
                    self.current_frame = frame
                    
                # Process frame (simulated object detection)
                height, width = frame.shape[:2]
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(
                    thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                objects = []
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:  # Filter small contours
                        x, y, w, h = cv2.boundingRect(contour)
                        confidence = min(area / (width * height) * 10, 1.0)
                        objects.append({
                            'label': 'object',
                            'confidence': confidence,
                            'box': (x, y, w, h)
                        })
                        
                # Update detected objects
                with self._lock:
                    self.detected_objects = objects
                    
                # Call callbacks
                for callback in self.callbacks:
                    try:
                        callback(frame, objects)
                    except Exception as e:
                        print(f"Error in vision callback: {e}")
                        
            except Exception as e:
                print(f"Error processing frame: {e}")
                time.sleep(0.1)
                
            # Maintain framerate
            time.sleep(1 / self.framerate)
