#!/usr/bin/env python3

import os
import threading
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.config import Config

class ConversationModule:
    """Conversation module for natural language processing and decision making"""
    
    def __init__(self, api_key: str = None, debug: bool = False):
        """
        Initialize Conversation module
        
        Args:
            api_key: OpenAI API key (optional, will use OPENAI_API_KEY from .env if not provided)
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Initialize OpenAI
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            if self.debug:
                print("OpenAI initialized")
        else:
            print("Warning: No OpenAI API key provided")
            self.client = None
            
        # Conversation state
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are Robbie the Robot, a robot who is being built by "
                          "Heidi and Heidi's daddy. Your responses should be short, "
                          "kind and helpful, and suitable for a second-grade student."
            }
        ]
        self.max_history = 10
        self.temperature = 0.7
        self.model = 'gpt-3.5-turbo'
        
    def chat(self, text: str) -> str:
        """
        Process text input and generate response
        
        Args:
            text: Input text
            
        Returns:
            Generated response
        """
        if not self.client:
            return "AI processing not available"
            
        with self._lock:
            try:
                # Add user message to history
                self.conversation_history.append({
                    'role': 'user',
                    'content': text
                })
                
                # Trim history if needed while preserving system message
                if len(self.conversation_history) > self.max_history:
                    # Separate system message from other messages
                    system_messages = [msg for msg in self.conversation_history if msg['role'] == 'system']
                    other_messages = [msg for msg in self.conversation_history if msg['role'] != 'system']
                    
                    # Keep only the last (max_history - len(system_messages)) non-system messages
                    other_messages = other_messages[-(self.max_history - len(system_messages)):]
                    
                    # Reconstruct history with system message(s) first
                    self.conversation_history = system_messages + other_messages
                    
                # Generate response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    temperature=self.temperature
                )
                
                # Extract response text
                response_text = response.choices[0].message.content
                
                # Add assistant response to history
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': response_text
                })
                
                return response_text
                
            except Exception as e:
                print(f"Error in AI processing: {e}")
                return f"Error: {str(e)}"
                
    def set_system_message(self, message: str) -> None:
        """Set the system message for the conversation"""
        # Remove any existing system messages
        self.conversation_history = [msg for msg in self.conversation_history if msg['role'] != 'system']
        
        # Add new system message at the start
        self.conversation_history.insert(0, {
            'role': 'system',
            'content': message
        })
        
    def set_temperature(self, temp: float) -> None:
        """Set the temperature for response generation"""
        self.temperature = temp
        
    def cleanup(self) -> None:
        """Clean up resources"""
        # Clear conversation history
        self.conversation_history = []
