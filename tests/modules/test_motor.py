import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.modules.motor import MotorModule

class TestMotorModule(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.mc = MotorModule(debug=True)
        
    def test_set_motor_speeds(self):
        """Test setting motor speeds"""
        self.mc.set_speeds(0.5, -0.5)
        self.assertEqual(self.mc.left_speed, 0.5)
        self.assertEqual(self.mc.right_speed, -0.5)
        
    def test_stop(self):
        """Test stopping motors"""
        self.mc.set_speeds(0.5, 0.5)
        self.mc.stop()
        self.assertEqual(self.mc.left_speed, 0.0)
        self.assertEqual(self.mc.right_speed, 0.0)
        
    def test_move_head(self):
        """Test head movement controls"""
        self.mc.move_head(pan=45, tilt=30)
        self.assertEqual(self.mc.head_pan, 45)
        self.assertEqual(self.mc.head_tilt, 30)
        
    def test_move_arm(self):
        """Test arm movement controls"""
        self.mc.move_arm("left", 0.8)
        self.assertEqual(self.mc.left_arm_position, 0.8)
        
        self.mc.move_arm("right", 0.6)
        self.assertEqual(self.mc.right_arm_position, 0.6)
        
    def test_speed_limits(self):
        """Test motor speed limits"""
        self.mc.set_speeds(1.5, -1.5)  # Should be clamped to [-1, 1]
        self.assertEqual(self.mc.left_speed, 1.0)
        self.assertEqual(self.mc.right_speed, -1.0)

if __name__ == '__main__':
    unittest.main()
