#!/usr/bin/env python3

import os
import yaml
from typing import Any, Dict, List, Optional, Union
import logging
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for robot settings"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config file, defaults to config.yaml in project root
        """
        if config_path is None:
            # Search for config.yaml starting from current file location up to root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
                candidate = os.path.join(current_dir, 'config.yaml')
                if os.path.exists(candidate):
                    config_path = candidate
                    break
                current_dir = os.path.dirname(current_dir)
            
            # Fallback to old behavior if not found
            if config_path is None:
                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(root_dir, 'config.yaml')

        self.config_path = config_path

        # Load config file
        try:
            with open(self.config_path, 'r') as f:
                loaded = yaml.safe_load(f)
                self.config = loaded if isinstance(loaded, dict) else {}
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
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

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration dictionary."""
        return dict(self.config) if isinstance(self.config, dict) else {}

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge ``updates`` into ``base`` without modifying unrelated keys."""
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and isinstance(base.get(key), dict)
            ):
                base[key] = self._deep_update(dict(base[key]), value)
            else:
                base[key] = value
        return base

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """Update configuration from a nested dict, then keep it in memory only.

        Call ``save()`` explicitly to persist to disk.
        """
        if not isinstance(updates, dict):
            logger.warning("Config.update_from_dict called with non-dict; ignoring")
            return
        if not isinstance(self.config, dict):
            self.config = {}
        self.config = self._deep_update(self.config, updates)

    def save(self) -> None:
        """Persist current configuration to the YAML file on disk."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.config, f, sort_keys=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
