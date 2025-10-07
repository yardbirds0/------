# -*- coding: utf-8 -*-
"""
Unit tests for Title Bar Model Selector ConfigController
Tests configuration management, CRUD operations, and signal emission
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from PySide6.QtCore import QCoreApplication

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.chat.controllers.config_controller import ConfigController


# Create QCoreApplication instance for Qt signals
app = QCoreApplication.instance() or QCoreApplication(sys.argv)


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_controller(temp_config_dir):
    """
    Create ConfigController instance with temporary config directory
    Reset singleton before and after test
    """
    # Reset singleton
    ConfigController._instance = None

    # Create controller
    controller = ConfigController.instance()
    original_path = controller.config_path
    controller.config_path = temp_config_dir / "ai_models.json"

    yield controller

    # Restore original path and reset singleton
    controller.config_path = original_path
    ConfigController._instance = None


class TestConfigControllerSingleton:
    """Test singleton pattern implementation"""

    def test_singleton_instance(self, config_controller):
        """Test that instance() returns same instance"""
        instance1 = ConfigController.instance()
        instance2 = ConfigController.instance()
        assert instance1 is instance2

    def test_direct_instantiation_raises_error(self, config_controller):
        """Test that direct instantiation raises RuntimeError"""
        with pytest.raises(RuntimeError, match="singleton"):
            ConfigController()


class TestGetCurrentModel:
    """Test get_current_model method"""

    def test_get_current_model_default(self, config_controller):
        """Test getting default model"""
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "siliconflow"
        assert "Qwen" in model_id

    def test_get_current_model_after_change(self, config_controller):
        """Test getting model after changing it"""
        config_controller.set_current_model("openai", "gpt-4-turbo")
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "openai"
        assert model_id == "gpt-4-turbo"


class TestSetCurrentModel:
    """Test set_current_model method"""

    def test_set_current_model_valid(self, config_controller):
        """Test setting valid model"""
        # Connect signal spy
        signal_spy = MagicMock()
        config_controller.model_changed.connect(signal_spy)

        # Set model
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Verify signal emitted
        signal_spy.assert_called_once_with("openai", "gpt-4-turbo")

        # Verify config updated
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "openai"
        assert model_id == "gpt-4-turbo"

    def test_set_current_model_invalid_provider(self, config_controller):
        """Test setting model with invalid provider"""
        # Connect error signal spy
        error_spy = MagicMock()
        config_controller.config_error.connect(error_spy)

        # Set invalid model
        config_controller.set_current_model("invalid_provider", "invalid_model")

        # Verify error signal emitted
        error_spy.assert_called_once()

    def test_set_current_model_queued_during_request(self, config_controller):
        """Test that model change is queued during active request"""
        # Set request active
        config_controller.set_request_active(True)

        # Try to set model
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Verify model not changed immediately
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "siliconflow"  # Still default

        # Verify change queued
        assert config_controller.pending_change == ("openai", "gpt-4-turbo")

        # Set request inactive
        config_controller.set_request_active(False)

        # Verify model changed now
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "openai"
        assert model_id == "gpt-4-turbo"


class TestGetProviders:
    """Test get_providers method"""

    def test_get_providers_sorted_by_order(self, config_controller):
        """Test that providers are sorted by order field"""
        providers = config_controller.get_providers()

        # Verify sorting
        for i in range(len(providers) - 1):
            assert providers[i]["order"] <= providers[i+1]["order"]

    def test_get_providers_returns_list(self, config_controller):
        """Test that get_providers returns a list"""
        providers = config_controller.get_providers()
        assert isinstance(providers, list)
        assert len(providers) >= 1


class TestGetProvider:
    """Test get_provider method"""

    def test_get_provider_existing(self, config_controller):
        """Test getting existing provider"""
        provider = config_controller.get_provider("siliconflow")
        assert provider is not None
        assert provider["id"] == "siliconflow"
        assert provider["name"] == "硅基流动"

    def test_get_provider_nonexistent(self, config_controller):
        """Test getting non-existent provider"""
        provider = config_controller.get_provider("nonexistent")
        assert provider is None


class TestAddProvider:
    """Test add_provider method"""

    def test_add_provider_valid(self, config_controller):
        """Test adding valid provider"""
        # Connect signal spy
        signal_spy = MagicMock()
        config_controller.provider_changed.connect(signal_spy)

        new_provider = {
            "id": "custom_provider",
            "name": "Custom Provider",
            "icon": "custom.png",
            "enabled": True,
            "api_key": "test_key",
            "api_url": "https://api.custom.com/v1",
            "models": []
        }

        config_controller.add_provider(new_provider)

        # Verify signal emitted
        signal_spy.assert_called_once_with("custom_provider")

        # Verify provider added
        provider = config_controller.get_provider("custom_provider")
        assert provider is not None
        assert provider["name"] == "Custom Provider"

    def test_add_provider_missing_id(self, config_controller):
        """Test adding provider without ID raises ValueError"""
        with pytest.raises(ValueError, match="must have an 'id'"):
            config_controller.add_provider({"name": "Test"})

    def test_add_provider_missing_name(self, config_controller):
        """Test adding provider without name raises ValueError"""
        with pytest.raises(ValueError, match="must have a 'name'"):
            config_controller.add_provider({"id": "test"})

    def test_add_provider_duplicate_id(self, config_controller):
        """Test adding provider with duplicate ID raises ValueError"""
        with pytest.raises(ValueError, match="already exists"):
            config_controller.add_provider({
                "id": "siliconflow",  # Already exists
                "name": "Duplicate"
            })


class TestUpdateProvider:
    """Test update_provider method"""

    def test_update_provider_existing(self, config_controller):
        """Test updating existing provider"""
        # Update provider
        config_controller.update_provider("siliconflow", {
            "api_key": "new_key",
            "enabled": False
        })

        # Verify update
        provider = config_controller.get_provider("siliconflow")
        assert provider["api_key"] == "new_key"
        assert provider["enabled"] is False

    def test_update_provider_nonexistent(self, config_controller):
        """Test updating non-existent provider raises ValueError"""
        with pytest.raises(ValueError, match="not found"):
            config_controller.update_provider("nonexistent", {"api_key": "test"})


class TestDeleteProvider:
    """Test delete_provider method"""

    def test_delete_provider_existing(self, config_controller):
        """Test deleting existing provider"""
        # Add a provider first
        config_controller.add_provider({
            "id": "to_delete",
            "name": "To Delete",
            "models": []
        })

        # Delete it
        config_controller.delete_provider("to_delete")

        # Verify deleted
        provider = config_controller.get_provider("to_delete")
        assert provider is None

    def test_delete_provider_nonexistent(self, config_controller):
        """Test deleting non-existent provider raises ValueError"""
        with pytest.raises(ValueError, match="not found"):
            config_controller.delete_provider("nonexistent")

    def test_delete_active_provider_clears_current(self, config_controller):
        """Test deleting active provider clears current model"""
        # Get default provider and model
        default_provider, default_model = config_controller.get_current_model()

        # Delete the default provider
        config_controller.delete_provider(default_provider)

        # Verify current cleared
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == ""
        assert model_id == ""


class TestReorderProviders:
    """Test reorder_providers method"""

    def test_reorder_providers(self, config_controller):
        """Test reordering providers"""
        # Get original order
        original_providers = config_controller.get_providers()
        original_ids = [p["id"] for p in original_providers]

        # Reverse order
        reversed_ids = list(reversed(original_ids))
        config_controller.reorder_providers(reversed_ids)

        # Verify new order
        new_providers = config_controller.get_providers()
        new_ids = [p["id"] for p in new_providers]
        assert new_ids == reversed_ids


class TestConfigPersistence:
    """Test configuration loading and saving"""

    def test_save_and_load_config(self, config_controller):
        """Test that configuration persists across save/load"""
        # Modify configuration
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Force save
        config_controller._save_config()

        # Verify file exists
        assert config_controller.config_path.exists()

        # Reload config
        config_controller._load_config()

        # Verify loaded correctly
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id == "openai"
        assert model_id == "gpt-4-turbo"

    def test_load_corrupted_config(self, config_controller, temp_config_dir):
        """Test loading corrupted JSON file"""
        # Create corrupted file
        config_path = temp_config_dir / "ai_models.json"
        with open(config_path, 'w') as f:
            f.write("{corrupted json")

        # Connect error signal spy
        error_spy = MagicMock()
        config_controller.config_error.connect(error_spy)

        # Load config
        config_controller._load_config()

        # Verify error signal emitted
        error_spy.assert_called_once()

        # Verify default config loaded
        provider_id, model_id = config_controller.get_current_model()
        assert provider_id != ""  # Should have default

    def test_atomic_write_creates_backup(self, config_controller):
        """Test that save creates backup file"""
        # Save configuration
        config_controller._save_config()

        # Modify and save again
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Verify backup exists
        backup_path = config_controller.config_path.with_suffix('.json.bak')
        assert backup_path.exists()


class TestDefaultConfig:
    """Test default configuration"""

    def test_default_config_has_providers(self, config_controller):
        """Test that default config includes providers"""
        providers = config_controller.get_providers()
        assert len(providers) >= 1

    def test_default_config_has_security_warning(self, config_controller):
        """Test that default config includes security warning"""
        assert "_security_warning" in config_controller.config

    def test_default_config_has_version(self, config_controller):
        """Test that default config includes version"""
        assert "version" in config_controller.config
        assert config_controller.config["version"] == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
