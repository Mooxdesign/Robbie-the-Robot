import unittest
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.modules.conversation import Conversation

class TestConversation(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Initialize Conversation module with API key from .env
        self.conversation = Conversation(debug=True)
        if not self.conversation.client:
            self.skipTest("OPENAI_API_KEY not set in .env file")
        print("OpenAI initialized")

    def test_chat_completion(self):
        """Test chat completion functionality"""
        # Test basic response
        response = self.conversation.chat("Say 'test passed'")
        self.assertIn("test passed", response.lower())

    def test_conversation_history(self):
        """Test conversation history management"""
        # Send multiple messages
        self.conversation.chat("Hello")
        self.conversation.chat("How are you?")
        
        # Check history length
        self.assertEqual(len(self.conversation.conversation_history), 4)  # 2 user messages + 2 responses

    def test_context_management(self):
        """Test context handling"""
        # Add system message
        self.conversation.set_system_message("You are a test bot. Always respond with 'Test OK'")
        
        # Check if system message is in history
        self.assertTrue(any(msg['role'] == 'system' for msg in self.conversation.conversation_history))
        
        # Test if system message affects responses
        response = self.conversation.chat("Hello")
        self.assertEqual(response, "Test OK")

    def test_temperature_setting(self):
        """Test temperature parameter"""
        # Test with different temperatures
        self.conversation.set_temperature(0.0)  # Deterministic
        
        # Same prompt should give same response with temperature 0
        response1 = self.conversation.chat("Say 'temperature test'")
        response2 = self.conversation.chat("Say 'temperature test'")
        self.assertEqual(response1, response2)

    def test_error_handling(self):
        """Test error handling"""
        # Test with invalid API key
        bad_conversation = Conversation(api_key="invalid_key", debug=True)
        response = bad_conversation.chat("Test message")
        self.assertIn("Error", response)

    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'conversation'):
            self.conversation.cleanup()
        print("AI cleanup completed")

if __name__ == '__main__':
    unittest.main()
