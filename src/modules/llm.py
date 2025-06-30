#!/usr/bin/env python3

import os
import logging
import threading
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from config import Config

class LlmModule:

    """Conversation module for natural language processing and decision making"""
    
    def __init__(self, api_key: str = None, debug: bool = False):
        """
        Initialize LLM module (OpenAI only)
        Args:
            api_key: OpenAI API key (optional, will use OPENAI_API_KEY from .env if not provided)
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            if self.debug:
                logger.info("OpenAI initialized")
        else:
            logger.warning("Warning: No OpenAI API key provided")
            self.client = None
        self.model = 'gpt-3.5-turbo'

    def chat_llm(self, messages, temperature=0.7):
        """
        Generate a response from the LLM given a message history.
        Args:
            messages: List of message dicts (role/content pairs)
            temperature: Sampling temperature
        Returns:
            Generated response text or error message
        """
        if not self.client:
            return "AI processing not available"
        with self._lock:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error in LLM processing: {e}")
                return f"Error: {str(e)}"



    def cleanup(self) -> None:
        """Clean up resources (no-op for LlmModule)"""
        pass
