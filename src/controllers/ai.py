#!/usr/bin/env python3

import os
import sys
import time
import threading
import openai
from typing import Optional, List, Dict, Any

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import Config

class AIController:
    """AI controller for natural language processing and decision making"""
    
    def __init__(self, debug: bool = False):
        """
        Initialize AI controller
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.api_key = config.get('ai', 'openai_api_key', default=None)
        self.model = config.get('ai', 'model', default='gpt-3.5-turbo')
        self.temperature = config.get('ai', 'temperature', default=0.7)
        self.max_tokens = config.get('ai', 'max_tokens', default=150)
        
        # Initialize OpenAI
        if self.api_key:
            openai.api_key = self.api_key
            if self.debug:
                print("OpenAI initialized")
        else:
            print("Warning: No OpenAI API key provided")
            
        # Conversation state
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are Robbie the Robot, a robot who is being built by "
                          "Heidi and Heidi's daddy. Your responses should be kind and "
                          "helpful, and suitable for a second-grade student."
            }
        ]
        self.max_history = config.get('ai', 'max_history', default=10)
        
    def process_text(self, text: str) -> str:
        """
        Process text input and generate response
        
        Args:
            text: Input text
            
        Returns:
            Generated response
        """
        if not self.api_key:
            return "AI processing not available"
            
        with self._lock:
            try:
                # Add user message to history
                self.conversation_history.append({
                    'role': 'user',
                    'content': text
                })
                
                # Trim history if needed
                if len(self.conversation_history) > self.max_history:
                    self.conversation_history = self.conversation_history[-self.max_history:]
                    
                # Generate response
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.conversation_history,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
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
                return "Sorry, I encountered an error"
                
    def clear_history(self):
        """Clear conversation history except system prompt"""
        with self._lock:
            self.conversation_history = self.conversation_history[:1]
            
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        with self._lock:
            return self.conversation_history.copy()
            
    def cleanup(self):
        """Clean up resources"""
        self.clear_history()
        if self.debug:
            print("AI cleanup completed")
