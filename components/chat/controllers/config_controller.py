# -*- coding: utf-8 -*-
"""
ConfigController - Centralized configuration management for AI models
Singleton pattern for consistent state management across the application
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PySide6.QtCore import QObject, Signal


class ConfigController(QObject):
    """
    Centralized configuration controller for AI model management

    Implements singleton pattern to ensure single source of truth for configuration.
    Handles loading, saving, and validating model configurations.

    Signals:
        model_changed: Emitted when active model changes (provider_id, model_id)
        provider_changed: Emitted when provider configuration changes (provider_id)
        config_loaded: Emitted when configuration is loaded successfully
        config_error: Emitted when configuration error occurs (error_message)
    """

    # Signals
    model_changed = Signal(str, str)      # (provider_id, model_id)
    provider_changed = Signal(str)        # provider_id
    config_loaded = Signal()
    config_error = Signal(str)            # error_message

    _instance: Optional['ConfigController'] = None

    @classmethod
    def instance(cls) -> 'ConfigController':
        """
        Get singleton instance of ConfigController

        Returns:
            ConfigController: The singleton instance
        """
        if cls._instance is None:
            cls._instance = ConfigController()
        return cls._instance

    def __init__(self):
        """
        Initialize ConfigController

        Raises:
            RuntimeError: If attempting to create multiple instances
        """
        if ConfigController._instance is not None:
            raise RuntimeError("ConfigController is a singleton. Use ConfigController.instance() instead.")

        super().__init__()

        # Configuration file path
        self.config_path = Path("config/ai_models.json")

        # Configuration data
        self.config: Dict = {}

        # Request state management
        self.request_active = False
        self.pending_change: Optional[Tuple[str, str]] = None

        # Load configuration on initialization
        self._load_config()

    def get_current_model(self) -> Tuple[str, str]:
        """
        Get currently active model

        Returns:
            Tuple[str, str]: (provider_id, model_id)
        """
        provider_id = self.config.get("current_provider", "")
        model_id = self.config.get("current_model", "")
        return (provider_id, model_id)

    def set_current_model(self, provider_id: str, model_id: str):
        """
        Set currently active model

        If a request is currently active, the change will be queued and applied
        after the request completes.

        Args:
            provider_id: Provider ID
            model_id: Model ID within the provider
        """
        if self.request_active:
            # Queue change for later
            self.pending_change = (provider_id, model_id)
            return

        # Validate provider and model exist
        if not self._validate_model_selection(provider_id, model_id):
            self.config_error.emit(f"Invalid model selection: {provider_id}/{model_id}")
            return

        # Update configuration
        self.config["current_provider"] = provider_id
        self.config["current_model"] = model_id

        # Save to file
        self._save_config()

        # Emit signal
        self.model_changed.emit(provider_id, model_id)

    def get_providers(self) -> List[Dict]:
        """
        Get list of all providers sorted by order

        Returns:
            List[Dict]: List of provider configurations
        """
        providers = self.config.get("providers", [])
        # Sort by order field
        return sorted(providers, key=lambda p: p.get("order", 999))

    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """
        Get specific provider configuration

        Args:
            provider_id: Provider ID

        Returns:
            Optional[Dict]: Provider configuration or None if not found
        """
        providers = self.config.get("providers", [])
        for provider in providers:
            if provider.get("id") == provider_id:
                return provider
        return None

    def add_provider(self, provider: Dict):
        """
        Add new provider to configuration

        Args:
            provider: Provider configuration dictionary

        Raises:
            ValueError: If provider data is invalid
        """
        # Validation
        if not provider.get("id"):
            raise ValueError("Provider must have an 'id' field")
        if not provider.get("name"):
            raise ValueError("Provider must have a 'name' field")

        # Check for duplicate ID
        existing_ids = [p.get("id") for p in self.config.get("providers", [])]
        if provider.get("id") in existing_ids:
            raise ValueError(f"Provider with id '{provider.get('id')}' already exists")

        # Add provider to list
        providers = self.config.setdefault("providers", [])
        provider["order"] = len(providers)
        providers.append(provider)

        # Save configuration
        self._save_config()

        # Emit signal
        self.provider_changed.emit(provider["id"])

    def update_provider(self, provider_id: str, provider_data: Dict):
        """
        Update existing provider configuration

        Args:
            provider_id: Provider ID to update
            provider_data: New provider data (partial update supported)
        """
        providers = self.config.get("providers", [])
        for i, provider in enumerate(providers):
            if provider.get("id") == provider_id:
                # Preserve order field
                order = provider.get("order", i)
                # Update provider data
                provider.update(provider_data)
                provider["order"] = order
                provider["id"] = provider_id  # Ensure ID doesn't change

                # Save configuration
                self._save_config()

                # Emit signal
                self.provider_changed.emit(provider_id)
                return

        raise ValueError(f"Provider '{provider_id}' not found")

    def delete_provider(self, provider_id: str):
        """
        Delete provider from configuration

        Args:
            provider_id: Provider ID to delete
        """
        providers = self.config.get("providers", [])

        # Filter out the provider
        updated_providers = [p for p in providers if p.get("id") != provider_id]

        if len(updated_providers) == len(providers):
            raise ValueError(f"Provider '{provider_id}' not found")

        self.config["providers"] = updated_providers

        # Reorder remaining providers
        self._reorder_providers()

        # If deleted provider was active, clear current selection
        if self.config.get("current_provider") == provider_id:
            self.config["current_provider"] = ""
            self.config["current_model"] = ""

        # Save configuration
        self._save_config()

        # Emit signal
        self.provider_changed.emit(provider_id)

    def reorder_providers(self, provider_ids: List[str]):
        """
        Reorder providers based on provided list of IDs

        Args:
            provider_ids: List of provider IDs in desired order
        """
        providers = self.config.get("providers", [])

        # Create ID to provider mapping
        provider_map = {p["id"]: p for p in providers}

        # Reorder providers
        reordered = []
        for idx, provider_id in enumerate(provider_ids):
            if provider_id in provider_map:
                provider = provider_map[provider_id]
                provider["order"] = idx
                reordered.append(provider)

        # Add any providers not in the reorder list
        existing_ids = set(provider_ids)
        for provider in providers:
            if provider["id"] not in existing_ids:
                provider["order"] = len(reordered)
                reordered.append(provider)

        self.config["providers"] = reordered

        # Save configuration
        self._save_config()

    def set_request_active(self, active: bool):
        """
        Set request active state

        When setting to False, applies any pending model changes.

        Args:
            active: Whether a request is currently active
        """
        self.request_active = active

        if not active and self.pending_change:
            # Apply pending change
            provider_id, model_id = self.pending_change
            self.pending_change = None
            self.set_current_model(provider_id, model_id)

    def _validate_model_selection(self, provider_id: str, model_id: str) -> bool:
        """
        Validate that provider and model exist in configuration

        Args:
            provider_id: Provider ID
            model_id: Model ID

        Returns:
            bool: True if valid, False otherwise
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        models = provider.get("models", [])
        model_ids = [m.get("id") for m in models]
        return model_id in model_ids

    def _load_config(self):
        """
        Load configuration from JSON file

        If file doesn't exist or is corrupted, loads default configuration.
        Emits config_loaded or config_error signal.
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.config_loaded.emit()
            else:
                # Load default configuration
                self.config = self._get_default_config()
                # Create config directory if it doesn't exist
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                # Save default configuration
                self._save_config()
                self.config_loaded.emit()
        except json.JSONDecodeError as e:
            # Corrupted JSON file
            error_msg = f"Configuration file corrupted: {e}"
            self.config_error.emit(error_msg)

            # Backup corrupted file
            backup_path = self.config_path.with_suffix('.json.corrupted')
            if self.config_path.exists():
                shutil.copy2(self.config_path, backup_path)

            # Load default configuration
            self.config = self._get_default_config()
            self._save_config()
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            self.config_error.emit(error_msg)
            self.config = self._get_default_config()

    def _save_config(self):
        """
        Save configuration to JSON file with atomic write

        Uses temporary file strategy to prevent corruption.
        Creates backup of existing file before overwriting.
        """
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write with temporary file
            temp_path = self.config_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            # Backup existing file
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.bak')
                shutil.copy2(self.config_path, backup_path)

            # Move temporary file to actual location
            temp_path.replace(self.config_path)

        except Exception as e:
            error_msg = f"Failed to save configuration: {e}"
            self.config_error.emit(error_msg)

    def _reorder_providers(self):
        """
        Reorder providers to ensure order values are sequential
        """
        providers = self.config.get("providers", [])
        for idx, provider in enumerate(sorted(providers, key=lambda p: p.get("order", 999))):
            provider["order"] = idx

    def _get_default_config(self) -> Dict:
        """
        Get default configuration with built-in models

        Returns:
            Dict: Default configuration with comprehensive model catalog
        """
        return {
            "version": "1.0",
            "_security_warning": "API keys are stored in plain text. Protect this file's permissions.",
            "current_provider": "siliconflow",
            "current_model": "Qwen/Qwen2.5-7B-Instruct",
            "providers": [
                {
                    "id": "siliconflow",
                    "name": "硅基流动",
                    "icon": "siliconflow.png",
                    "enabled": True,
                    "api_key": "",
                    "api_url": "https://api.siliconflow.cn/v1",
                    "website": "https://siliconflow.cn",
                    "models": [
                        # DeepSeek 系列
                        {
                            "id": "deepseek-ai/DeepSeek-V2.5",
                            "name": "DeepSeek-V2.5",
                            "category": "DeepSeek",
                            "context_length": 32768,
                            "max_tokens": 4096
                        },
                        {
                            "id": "deepseek-ai/DeepSeek-Coder-V2-Instruct",
                            "name": "DeepSeek-Coder-V2",
                            "category": "DeepSeek",
                            "context_length": 16384,
                            "max_tokens": 4096
                        },
                        # Qwen 系列
                        {
                            "id": "Qwen/Qwen2.5-7B-Instruct",
                            "name": "Qwen2.5-7B-Instruct",
                            "category": "Qwen",
                            "context_length": 131072,
                            "max_tokens": 4096
                        },
                        {
                            "id": "Qwen/Qwen2.5-14B-Instruct",
                            "name": "Qwen2.5-14B-Instruct",
                            "category": "Qwen",
                            "context_length": 131072,
                            "max_tokens": 8192
                        },
                        {
                            "id": "Qwen/Qwen2.5-32B-Instruct",
                            "name": "Qwen2.5-32B-Instruct",
                            "category": "Qwen",
                            "context_length": 131072,
                            "max_tokens": 8192
                        },
                        {
                            "id": "Qwen/Qwen2.5-72B-Instruct",
                            "name": "Qwen2.5-72B-Instruct",
                            "category": "Qwen",
                            "context_length": 131072,
                            "max_tokens": 8192
                        },
                        # Llama-3.2 系列
                        {
                            "id": "meta-llama/Llama-3.2-1B-Instruct",
                            "name": "Llama-3.2-1B-Instruct",
                            "category": "Llama-3.2",
                            "context_length": 131072,
                            "max_tokens": 2048
                        },
                        {
                            "id": "meta-llama/Llama-3.2-3B-Instruct",
                            "name": "Llama-3.2-3B-Instruct",
                            "category": "Llama-3.2",
                            "context_length": 131072,
                            "max_tokens": 2048
                        },
                        # Gemma 系列
                        {
                            "id": "google/gemma-2-9b-it",
                            "name": "Gemma-2-9B-IT",
                            "category": "Gemma",
                            "context_length": 8192,
                            "max_tokens": 4096
                        },
                        {
                            "id": "google/gemma-2-27b-it",
                            "name": "Gemma-2-27B-IT",
                            "category": "Gemma",
                            "context_length": 8192,
                            "max_tokens": 4096
                        },
                        # BAAI 系列
                        {
                            "id": "BAAI/bge-large-zh-v1.5",
                            "name": "BGE-Large-ZH-V1.5",
                            "category": "BAAI",
                            "context_length": 512,
                            "max_tokens": 512
                        },
                        {
                            "id": "BAAI/bge-base-zh-v1.5",
                            "name": "BGE-Base-ZH-V1.5",
                            "category": "BAAI",
                            "context_length": 512,
                            "max_tokens": 512
                        },
                        # Embedding 系列
                        {
                            "id": "BAAI/bge-m3",
                            "name": "BGE-M3",
                            "category": "Embedding",
                            "context_length": 8192,
                            "max_tokens": 512
                        },
                        {
                            "id": "sentence-transformers/all-MiniLM-L6-v2",
                            "name": "All-MiniLM-L6-V2",
                            "category": "Embedding",
                            "context_length": 512,
                            "max_tokens": 512
                        }
                    ],
                    "order": 0
                },
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "icon": "openai.png",
                    "enabled": False,
                    "api_key": "",
                    "api_url": "https://api.openai.com/v1",
                    "website": "https://platform.openai.com",
                    "models": [
                        {
                            "id": "gpt-4-turbo",
                            "name": "GPT-4 Turbo",
                            "category": "Openai",
                            "context_length": 128000,
                            "max_tokens": 4096
                        },
                        {
                            "id": "gpt-4",
                            "name": "GPT-4",
                            "category": "Openai",
                            "context_length": 8192,
                            "max_tokens": 4096
                        },
                        {
                            "id": "gpt-3.5-turbo",
                            "name": "GPT-3.5 Turbo",
                            "category": "Openai",
                            "context_length": 16385,
                            "max_tokens": 4096
                        },
                        {
                            "id": "text-embedding-3-large",
                            "name": "Text-Embedding-3-Large",
                            "category": "Embedding",
                            "context_length": 8191,
                            "max_tokens": 8191
                        },
                        {
                            "id": "text-embedding-3-small",
                            "name": "Text-Embedding-3-Small",
                            "category": "Embedding",
                            "context_length": 8191,
                            "max_tokens": 8191
                        }
                    ],
                    "order": 1
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic",
                    "icon": "anthropic.png",
                    "enabled": False,
                    "api_key": "",
                    "api_url": "https://api.anthropic.com/v1",
                    "website": "https://www.anthropic.com",
                    "models": [
                        {
                            "id": "claude-3-5-sonnet-20241022",
                            "name": "Claude 3.5 Sonnet",
                            "category": "Anthropic",
                            "context_length": 200000,
                            "max_tokens": 8192
                        },
                        {
                            "id": "claude-3-opus-20240229",
                            "name": "Claude 3 Opus",
                            "category": "Anthropic",
                            "context_length": 200000,
                            "max_tokens": 4096
                        },
                        {
                            "id": "claude-3-haiku-20240307",
                            "name": "Claude 3 Haiku",
                            "category": "Anthropic",
                            "context_length": 200000,
                            "max_tokens": 4096
                        }
                    ],
                    "order": 2
                },
                {
                    "id": "google",
                    "name": "Google",
                    "icon": "google.png",
                    "enabled": False,
                    "api_key": "",
                    "api_url": "https://generativelanguage.googleapis.com/v1",
                    "website": "https://ai.google.dev",
                    "models": [
                        {
                            "id": "gemini-1.5-pro",
                            "name": "Gemini 1.5 Pro",
                            "category": "Gemini",
                            "context_length": 2097152,
                            "max_tokens": 8192
                        },
                        {
                            "id": "gemini-1.5-flash",
                            "name": "Gemini 1.5 Flash",
                            "category": "Gemini",
                            "context_length": 1048576,
                            "max_tokens": 8192
                        },
                        {
                            "id": "gemini-1.0-pro",
                            "name": "Gemini 1.0 Pro",
                            "category": "Gemini",
                            "context_length": 32760,
                            "max_tokens": 2048
                        }
                    ],
                    "order": 3
                },
                {
                    "id": "doubao",
                    "name": "豆包",
                    "icon": "doubao.png",
                    "enabled": False,
                    "api_key": "",
                    "api_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "website": "https://www.volcengine.com/product/doubao",
                    "models": [
                        {
                            "id": "doubao-pro-32k",
                            "name": "豆包-Pro-32K",
                            "category": "Doubao",
                            "context_length": 32768,
                            "max_tokens": 4096
                        },
                        {
                            "id": "doubao-lite-32k",
                            "name": "豆包-Lite-32K",
                            "category": "Doubao",
                            "context_length": 32768,
                            "max_tokens": 4096
                        }
                    ],
                    "order": 4
                }
            ]
        }
