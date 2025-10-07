# -*- coding: utf-8 -*-
"""
Configuration Controller
Manages application configuration with Pydantic validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChatConfig(BaseModel):
    """
    Chat configuration model with validation

    All settings are validated by Pydantic and persisted to JSON
    """

    # Display settings
    theme: str = Field(default='light', description="UI theme (light/dark)")
    font_size: int = Field(default=14, ge=12, le=18, description="Font size in pixels")

    # AI settings
    active_service: str = Field(default='openai', description="Active AI service name")
    context_messages: int = Field(default=5, ge=0, le=10, description="Number of context messages")
    temperature: float = Field(default=0.7, ge=0, le=2, description="AI temperature parameter")
    max_tokens: int = Field(default=2048, ge=100, le=8000, description="Maximum tokens for AI response")

    # Features
    cot_enabled: bool = Field(default=False, description="Chain of Thought enabled")
    auto_save: bool = Field(default=True, description="Auto-save conversations")

    class Config:
        extra = 'forbid'  # Reject unknown fields
        validate_assignment = True  # Validate on assignment


class ConfigController:
    """
    Configuration management controller

    Features:
    - Load/save configuration from/to JSON
    - Pydantic validation
    - Immediate effect on value changes
    - Migration support
    """

    def __init__(self, config_path: str = "config/chat_config.json"):
        """
        Initialize configuration controller

        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = Path(config_path)
        self.config: ChatConfig = self.load()

    def load(self) -> ChatConfig:
        """
        Load configuration from file

        Creates default config if file doesn't exist.
        Handles migration from old formats.

        Returns:
            ChatConfig instance
        """
        if not self.config_path.exists():
            logger.info(f"Config file not found, using defaults: {self.config_path}")
            return ChatConfig()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Migration support: handle old format
            data = self._migrate_config(data)

            config = ChatConfig(**data)
            logger.info(f"Configuration loaded from: {self.config_path}")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Using default configuration")
            return ChatConfig()

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return ChatConfig()

    def save(self):
        """
        Save configuration to file

        Creates parent directories if needed.
        Writes with UTF-8 encoding and pretty formatting.
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Save with pretty formatting
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.config.model_dump(),  # Pydantic v2 uses model_dump()
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            logger.info(f"Configuration saved to: {self.config_path}")

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """
        Set configuration value with immediate save

        Args:
            key: Configuration key
            value: New value

        Raises:
            ValueError: If validation fails
        """
        try:
            setattr(self.config, key, value)
            self.save()
            logger.info(f"Config updated: {key} = {value}")

        except Exception as e:
            logger.error(f"Error setting config {key}={value}: {e}")
            raise

    def _migrate_config(self, data: dict) -> dict:
        """
        Migrate configuration from old format

        Args:
            data: Raw configuration data

        Returns:
            Migrated configuration data
        """
        # Example migration: rename old keys
        migrations = {
            'ai_model': 'active_service',
            'num_context': 'context_messages',
        }

        for old_key, new_key in migrations.items():
            if old_key in data and new_key not in data:
                data[new_key] = data.pop(old_key)
                logger.info(f"Migrated config: {old_key} -> {new_key}")

        return data

    def reset_to_default(self):
        """
        Reset configuration to default values
        """
        self.config = ChatConfig()
        self.save()
        logger.info("Configuration reset to defaults")

    def get_all(self) -> dict:
        """
        Get all configuration as dictionary

        Returns:
            Dictionary of all config values
        """
        return self.config.model_dump()
