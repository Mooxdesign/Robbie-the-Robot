import unittest
import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import all controller tests
from tests.modules.test_motor import TestMotorModule
from tests.modules.test_vision import TestVisionModule
from tests.modules.test_audio import TestAudioModule
from tests.modules.test_conversation import TestConversationModule
from tests.modules.test_lights import TestLedsModule

def create_test_suite():
    """Create test suite with all controller tests"""
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMotorModule))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVisionModule))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAudioModule))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConversationModule))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLedsModule))
    
    return suite

if __name__ == '__main__':
    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    test_suite = create_test_suite()
    runner.run(test_suite)
