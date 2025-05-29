import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
from unittest.mock import MagicMock, patch
import time
import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
modules_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/modules'))
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from src.modules.leds import LedsModule

class TestLedsModule(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.lc = LedsModule(debug=True)
        
    def test_set_color(self):
        """Test setting light colors"""
        # Test RGB values
        self.lc.set_color(255, 0, 0)  # Red
        self.assertEqual(self.lc.requested_color, (255, 0, 0))
        brightness = getattr(self.lc.unicorn, 'brightness', 1.0) if hasattr(self.lc, 'unicorn') and self.lc.unicorn else 1.0
        scaled = (round(255 * brightness), 0, 0)
        self.assertEqual(self.lc.current_color, scaled)

        self.lc.set_color(0, 255, 0)  # Green
        self.assertEqual(self.lc.requested_color, (0, 255, 0))
        scaled = (0, round(255 * brightness), 0)
        self.assertEqual(self.lc.current_color, scaled)

        
    def test_color_validation(self):
        """Test color value validation"""
        # Test invalid values
        with self.assertRaises(ValueError):
            self.lc.set_color(300, 0, 0)  # Too high
            
        with self.assertRaises(ValueError):
            self.lc.set_color(-1, 0, 0)  # Negative
            
    def test_animations(self):
        """Test light animations"""
        # Test pulse animation
        self.lc.start_pulse(255, 0, 0, duration=0.1)
        time.sleep(0.2)
        self.lc.stop_animation()
        
        # Test rainbow animation
        self.lc.start_rainbow(duration=0.1)
        time.sleep(0.2)
        self.lc.stop_animation()
        
    def test_brightness(self):
        """Test brightness control"""
        # Set full brightness
        self.lc.set_brightness(1.0)
        self.lc.set_color(255, 255, 255)
        self.assertEqual(self.lc.requested_color, (255, 255, 255))
        self.assertEqual(self.lc.current_color, (255, 255, 255))
        
        # Set half brightness
        self.lc.set_brightness(0.5)
        self.lc.set_color(255, 255, 255)
        self.assertEqual(self.lc.requested_color, (255, 255, 255))
        self.assertEqual(self.lc.current_color, (128, 128, 128))

        
    def test_cleanup(self):
        """Test cleanup"""
        self.lc.start_rainbow()
        self.lc.cleanup()
        self.assertFalse(self.lc.animation_running)
        
    def tearDown(self):
        """Clean up after each test"""
        self.lc.cleanup()

if __name__ == '__main__':
    unittest.main()
