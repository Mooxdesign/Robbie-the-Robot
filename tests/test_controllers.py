import os
import sys
import time
import unittest
import numpy as np
from unittest.mock import MagicMock, patch
import matplotlib.pyplot as plt

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Import simulation first to set verbosity
from simulation import hardware
hardware.VERBOSE = False  # Disable simulation output by default during tests

from controllers.motor import MotorController
from controllers.voice import VoiceController
from controllers.vision import VisionController
from controllers.lights import LightController
from controllers.ai import AIController
from controllers.audio import AudioController
from robot_controller import RobotController

class TestMotorController(unittest.TestCase):
    def setUp(self):
        self.mc = MotorController()
    
    def test_motor_limits(self):
        """Test that motor speeds are properly limited"""
        self.mc.set_motor_speeds(1.5, -1.5)
        self.assertEqual(self.mc.left_speed, 1.0)
        self.assertEqual(self.mc.right_speed, -1.0)
        
        self.mc.set_motor_speeds(-2.0, 2.0)
        self.assertEqual(self.mc.left_speed, -1.0)
        self.assertEqual(self.mc.right_speed, 1.0)
        
    def test_motor_stop(self):
        """Test motor stop functionality"""
        self.mc.set_motor_speeds(0.5, 0.5)
        self.mc.stop()
        self.assertEqual(self.mc.left_speed, 0.0)
        self.assertEqual(self.mc.right_speed, 0.0)

class TestVoiceController(unittest.TestCase):
    @patch('pyttsx3.init')
    def test_speak(self, mock_init):
        """Test text-to-speech functionality"""
        mock_engine = MagicMock()
        mock_init.return_value = mock_engine
        
        vc = VoiceController()
        vc.engine = mock_engine  # Replace the engine directly
        
        vc.speak("Hello", blocking=True)
        mock_engine.say.assert_called_once_with("Hello")
        mock_engine.runAndWait.assert_called_once()

class TestVisionController(unittest.TestCase):
    def setUp(self):
        self.vc = VisionController()
        self.vc.start()  # Start vision processing
    
    def tearDown(self):
        self.vc.stop()  # Stop vision processing
    
    def test_get_frame(self):
        """Test image capture"""
        # Give the camera a moment to start
        time.sleep(0.1)
        frame = self.vc.get_frame()
        self.assertIsNotNone(frame)

class TestLightController(unittest.TestCase):
    def setUp(self):
        self.lc = LightController()
    
    def test_set_all(self):
        """Test setting all LEDs to a color"""
        self.lc.set_all(255, 0, 0)  # Set all to red
        self.assertEqual(self.lc.buffer[0, 0].tolist(), [255, 0, 0])
    
    def test_clear(self):
        """Test clearing all LEDs"""
        self.lc.set_all(255, 0, 0)
        self.lc.clear()
        self.assertEqual(self.lc.buffer[0, 0].tolist(), [0, 0, 0])

class TestAIController(unittest.TestCase):
    def setUp(self):
        self.ai = AIController()
    
    def test_process_text(self):
        """Test text processing"""
        response = self.ai.process_text("Hello")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

class TestAudioController(unittest.TestCase):
    def setUp(self):
        self.ac = AudioController()
    
    def test_play_sound(self):
        """Test sound playback"""
        # Since we're in simulation mode, this should not raise any errors
        self.ac.play_sound("beep")

class TestRobotIntegration(unittest.TestCase):
    def setUp(self):
        """Initialize robot for each test"""
        self.robot = RobotController()
    
    def tearDown(self):
        """Clean up after each test"""
        self.robot.cleanup()
    
    def test_motor_movement(self):
        """Test basic motor movement sequences"""
        # Test forward/backward
        self.robot.set_motor_speeds(0.5, 0.5)  # Forward
        time.sleep(0.1)
        self.robot.set_motor_speeds(-0.5, -0.5)  # Backward
        time.sleep(0.1)
        
        # Test turning
        self.robot.set_motor_speeds(0.3, -0.3)  # Turn right
        time.sleep(0.1)
        self.robot.set_motor_speeds(-0.3, 0.3)  # Turn left
        time.sleep(0.1)
        
        # Stop
        self.robot.set_motor_speeds(0, 0)
    
    def test_head_movement(self):
        """Test head servo movement"""
        # Test pan/tilt movements
        self.robot.move_head(pan=0.5, tilt=0.2)
        time.sleep(0.1)
        self.robot.move_head(pan=-0.5, tilt=-0.2)
        time.sleep(0.1)
        self.robot.move_head(pan=0, tilt=0)
    
    def test_arm_movement(self):
        """Test arm servo movement"""
        # Test both arms
        self.robot.move_arm("left", 0.8)
        time.sleep(0.1)
        self.robot.move_arm("right", 0.8)
        time.sleep(0.1)
        self.robot.move_arm("left", 0)
        self.robot.move_arm("right", 0)
    
    def test_voice_interaction(self):
        """Test voice interaction capabilities"""
        # Test speech output
        self.robot.say("Hello, I am your robot assistant")
        time.sleep(0.1)
        
        # Test speech recognition and AI response
        # Note: In simulation mode, this will likely return no speech
        text = self.robot.listen(timeout=1)
        if text:
            response = self.robot.process_text(text)
            self.assertIsInstance(response, str)
            self.assertTrue(len(response) > 0)

if __name__ == '__main__':
    # Check if we should run visualization test or unit tests
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Run unit tests
        unittest.main(argv=['first-arg-is-ignored'])
    else:
        # Run visualization test
        print("Running visualization test...")
        robot = RobotController()
        
        # Get visualizer
        from simulation.visualizer import get_visualizer
        vis = get_visualizer()
        
        try:
            # Test motor movement
            print("\nTesting motor movement...")
            for i in range(20):
                speed = np.sin(i * 0.5)
                robot.set_motor_speeds(speed, -speed)
                plt.pause(0.05)  # Faster updates
            
            # Test head movement
            print("\nTesting head movement...")
            for i in range(20):
                pan = np.sin(i * 0.5) * 90  # -90 to 90 degrees
                tilt = np.cos(i * 0.5) * 45  # -45 to 45 degrees
                robot.move_head(pan=pan, tilt=tilt)
                plt.pause(0.05)
            
            # Test arm movement
            print("\nTesting arm movement...")
            for i in range(20):
                pos = (np.sin(i * 0.5) + 1) / 2  # 0 to 1
                robot.move_arm("left", pos)
                robot.move_arm("right", 1-pos)
                plt.pause(0.05)
            
            print("\nVisualization test complete. Press Ctrl+C to exit.")
            while True:
                plt.pause(0.1)
                
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        finally:
            # Clean up
            plt.close('all')
