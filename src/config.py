#!/usr/bin/env python3

import os
import yaml
from typing import Any, Dict, List, Optional, Union

class Config:
    """Configuration manager for robot settings"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config file, defaults to config.yaml in project root
        """
        if config_path is None:
            # Get project root directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root_dir, 'config.yaml')
            
        # Load config file
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}")
            self.config = {}
            
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get value from config
        
        Args:
            *keys: Key path to value
            default: Default value if not found
            
        Returns:
            Config value or default
        """
        value = self.config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
        return value
