#!/usr/bin/env python3

import os
import sys
import time
import threading
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class RobotVisualizer:
    """Visualizes robot state in simulation mode"""
    
    def __init__(self):
        """Initialize visualizer"""
        # Robot state
        self.motor_speeds = [0, 0]  # Left, Right
        self.head_position = [0, 0]  # Pan, Tilt
        self.arm_positions = [0, 0]  # Left, Right
        self.camera_frame = np.zeros((480, 640, 3))
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Create figure
        self.fig, ((self.motor_ax, self.head_ax), 
                  (self.arm_ax, self.camera_ax)) = plt.subplots(2, 2, figsize=(12, 8))
        
        # Motor subplot
        self.motor_ax.set_title('DC Motors')
        self.motor_ax.set_xlim(-1.2, 1.2)
        self.motor_ax.set_ylim(-0.2, 0.2)
        self.motor_bars = self.motor_ax.barh(['Left', 'Right'], [0, 0])
        
        # Head servo subplot
        self.head_ax.set_title('Head Position')
        self.head_ax.set_xlim(-100, 100)
        self.head_ax.set_ylim(-100, 100)
        self.head_point, = self.head_ax.plot([0], [0], 'ro')
        self.head_ax.grid(True)
        
        # Arm subplot
        self.arm_ax.set_title('Arm Positions')
        self.arm_ax.set_xlim(-0.2, 1.2)
        self.arm_ax.set_ylim(-0.2, 0.2)
        self.arm_bars = self.arm_ax.barh(['Left', 'Right'], [0, 0])
        
        # Camera view subplot
        self.camera_ax.set_title('Camera View')
        self.camera_image = self.camera_ax.imshow(np.zeros((480, 640, 3)))
        
        # Adjust layout
        self.fig.tight_layout()
        
        # Start animation
        self.animation = FuncAnimation(
            self.fig, self._update_plot,
            interval=50,  # 20 FPS
            blit=False
        )
        
        # Show plot
        plt.show(block=False)
        plt.pause(0.1)  # Small pause to let the window appear
    
    def _update_plot(self, frame):
        """Update all plots"""
        with self._lock:
            # Update motor bars
            for i, speed in enumerate(self.motor_speeds):
                self.motor_bars[i].set_width(speed)
                self.motor_bars[i].set_color('g' if speed >= 0 else 'r')
            
            # Update head position
            self.head_point.set_data([self.head_position[0]], [self.head_position[1]])
            
            # Update arm bars
            for i, pos in enumerate(self.arm_positions):
                self.arm_bars[i].set_width(pos)
                self.arm_bars[i].set_color('b')
            
            # Update camera frame
            self.camera_image.set_array(self.camera_frame)
    
    def set_motor_speeds(self, left: Optional[float], right: Optional[float]):
        """Update motor speeds"""
        with self._lock:
            if left is not None:
                self.motor_speeds[0] = left
            if right is not None:
                self.motor_speeds[1] = right
    
    def set_head_position(self, pan: Optional[float], tilt: Optional[float]):
        """Update head servo position"""
        with self._lock:
            if pan is not None:
                self.head_position[0] = pan
            if tilt is not None:
                self.head_position[1] = tilt
    
    def set_arm_position(self, side: str, position: float):
        """Update arm position"""
        with self._lock:
            if side.lower() == 'left':
                self.arm_positions[0] = position
            else:
                self.arm_positions[1] = position
    
    def set_camera_frame(self, frame: np.ndarray):
        """Update camera frame"""
        with self._lock:
            self.camera_frame = frame
    
    def cleanup(self):
        """Clean up resources"""
        plt.close(self.fig)

# Global visualizer instance
visualizer = None

def get_visualizer() -> RobotVisualizer:
    """Get or create visualizer instance"""
    global visualizer
    if visualizer is None:
        visualizer = RobotVisualizer()
    return visualizer
