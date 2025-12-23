from modules.llm import LlmModule
from config import Config
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class ConversationController:
    def __init__(self, debug=False, api_key=None):
        self.llm = LlmModule(api_key=api_key, debug=debug)
        self.debug = debug
        
        # Load config
        config = Config()
        
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are Robbie the Robot, a kind but goofy robot built by Heidi and Heidi's daddy. Your responses should be interesting, and suitable for a 10 year old. No sound effects like 'beep boop'. You are also fascinated by space. "
            }
        ]
        self.max_history = config.get('ai', 'max_history', default=10)
        self.temperature = config.get('ai', 'temperature', default=0.7)

    def chat(self, text):
        # Add user message
        self.conversation_history.append({'role': 'user', 'content': text})
        # Broadcast updated chat history after user message
        self._broadcast_chat_history('user')
        # Trim history if needed while preserving system message
        if len(self.conversation_history) > self.max_history:
            # Split into system and non-system messages
            system_messages = [msg for msg in self.conversation_history if msg['role'] == 'system']
            other_messages = [msg for msg in self.conversation_history if msg['role'] != 'system']
            # Keep only the last (max_history - len(system_messages)) non-system messages
            other_messages = other_messages[-(self.max_history - len(system_messages)):]
            # Reconstruct history with system message(s) first
            self.conversation_history = system_messages + other_messages
        # Get LLM response
        response_text = self.llm.chat_llm(self.conversation_history, temperature=self.temperature)
        # Add assistant response
        self.conversation_history.append({'role': 'assistant', 'content': response_text})
        # Broadcast updated chat history after assistant reply
        self._broadcast_chat_history('assistant')
        return response_text

    def _broadcast_chat_history(self, sender):
        """Broadcast chat history to API clients if available."""
        try:
            from api.app import robot_state, manager
            robot_state["chat_history"] = self.get_chat_history()
            
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(manager.broadcast(json.dumps({
                    "type": "chat_history",
                    "chat_history": robot_state["chat_history"]
                })))
            except RuntimeError:
                pass
        except ImportError:
            pass
        except Exception as e:
            if self.debug:
                logger.error(f"Failed to broadcast chat history: {e}")


    def cleanup(self):
        self.conversation_history = []

    def get_chat_history(self):
        # Convert OpenAI roles to 'user'/'robot' for the UI, skipping system messages
        chat_history = []
        for msg in self.conversation_history:
            if msg['role'] == 'user':
                chat_history.append({'sender': 'user', 'text': msg['content']})
            elif msg['role'] == 'assistant':
                chat_history.append({'sender': 'robot', 'text': msg['content']})
        return chat_history

