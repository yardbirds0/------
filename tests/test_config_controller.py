# -*- coding: utf-8 -*-
"""
Unit Tests for Configuration Controller
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from controllers.config_controller import ConfigController, ChatConfig
from pydantic import ValidationError


class TestChatConfig(unittest.TestCase):
    """Test cases for ChatConfig Pydantic model"""

    def test_default_values(self):
        """Test default configuration values"""
        config = ChatConfig()

        self.assertEqual(config.theme, 'light')
        self.assertEqual(config.font_size, 14)
        self.assertEqual(config.active_service, 'openai')
        self.assertEqual(config.context_messages, 5)
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.max_tokens, 2048)
        self.assertEqual(config.cot_enabled, False)
        self.assertEqual(config.auto_save, True)

    def test_custom_values(self):
        """Test custom configuration values"""
        config = ChatConfig(
            theme='dark',
            font_size=16,
            temperature=1.0,
            max_tokens=4096
        )

        self.assertEqual(config.theme, 'dark')
        self.assertEqual(config.font_size, 16)
        self.assertEqual(config.temperature, 1.0)
        self.assertEqual(config.max_tokens, 4096)

    def test_validation_font_size(self):
        """Test font_size validation"""
        # Valid range: 12-18
        ChatConfig(font_size=12)  # Should not raise
        ChatConfig(font_size=18)  # Should not raise

        with self.assertRaises(ValidationError):
            ChatConfig(font_size=10)  # Too small

        with self.assertRaises(ValidationError):
            ChatConfig(font_size=20)  # Too large

    def test_validation_temperature(self):
        """Test temperature validation"""
        # Valid range: 0-2
        ChatConfig(temperature=0.0)  # Should not raise
        ChatConfig(temperature=2.0)  # Should not raise

        with self.assertRaises(ValidationError):
            ChatConfig(temperature=-0.1)  # Too small

        with self.assertRaises(ValidationError):
            ChatConfig(temperature=2.1)  # Too large

    def test_validation_context_messages(self):
        """Test context_messages validation"""
        # Valid range: 0-10
        ChatConfig(context_messages=0)  # Should not raise
        ChatConfig(context_messages=10)  # Should not raise

        with self.assertRaises(ValidationError):
            ChatConfig(context_messages=-1)  # Too small

        with self.assertRaises(ValidationError):
            ChatConfig(context_messages=11)  # Too large

    def test_validation_max_tokens(self):
        """Test max_tokens validation"""
        # Valid range: 100-8000
        ChatConfig(max_tokens=100)  # Should not raise
        ChatConfig(max_tokens=8000)  # Should not raise

        with self.assertRaises(ValidationError):
            ChatConfig(max_tokens=50)  # Too small

        with self.assertRaises(ValidationError):
            ChatConfig(max_tokens=10000)  # Too large

    def test_forbid_extra_fields(self):
        """Test that extra fields are rejected"""
        with self.assertRaises(ValidationError):
            ChatConfig(unknown_field='value')


class TestConfigController(unittest.TestCase):
    """Test cases for ConfigController"""

    def setUp(self):
        """Create temporary config file for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)

    def test_load_default_when_no_file(self):
        """Test loading default config when file doesn't exist"""
        controller = ConfigController(self.config_path)

        self.assertIsNotNone(controller.config)
        self.assertEqual(controller.config.theme, 'light')
        self.assertEqual(controller.config.font_size, 14)

    def test_save_and_load(self):
        """Test saving and loading configuration"""
        # Create controller and modify config
        controller1 = ConfigController(self.config_path)
        controller1.config.theme = 'dark'
        controller1.config.font_size = 16
        controller1.save()

        # Load in new controller instance
        controller2 = ConfigController(self.config_path)

        self.assertEqual(controller2.config.theme, 'dark')
        self.assertEqual(controller2.config.font_size, 16)

    def test_get_method(self):
        """Test get() method"""
        controller = ConfigController(self.config_path)

        self.assertEqual(controller.get('theme'), 'light')
        self.assertEqual(controller.get('font_size'), 14)
        self.assertIsNone(controller.get('nonexistent'))
        self.assertEqual(controller.get('nonexistent', 'default'), 'default')

    def test_set_method(self):
        """Test set() method with immediate save"""
        controller = ConfigController(self.config_path)

        # Set value
        controller.set('theme', 'dark')

        # Verify it's saved
        self.assertTrue(os.path.exists(self.config_path))

        # Load in new controller
        controller2 = ConfigController(self.config_path)
        self.assertEqual(controller2.config.theme, 'dark')

    def test_set_invalid_value(self):
        """Test set() method with invalid value"""
        controller = ConfigController(self.config_path)

        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            controller.set('font_size', 100)  # Out of range

    def test_migration(self):
        """Test configuration migration from old format"""
        # Create old format config
        old_config = {
            'ai_model': 'gemini',  # Old key
            'num_context': 8,      # Old key
            'theme': 'dark'
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(old_config, f)

        # Load with migration
        controller = ConfigController(self.config_path)

        # Verify migration
        self.assertEqual(controller.config.active_service, 'gemini')
        self.assertEqual(controller.config.context_messages, 8)
        self.assertEqual(controller.config.theme, 'dark')

    def test_reset_to_default(self):
        """Test resetting to default configuration"""
        controller = ConfigController(self.config_path)

        # Modify config
        controller.config.theme = 'dark'
        controller.config.font_size = 18

        # Reset
        controller.reset_to_default()

        # Verify reset
        self.assertEqual(controller.config.theme, 'light')
        self.assertEqual(controller.config.font_size, 14)

    def test_get_all(self):
        """Test get_all() method"""
        controller = ConfigController(self.config_path)

        all_config = controller.get_all()

        self.assertIsInstance(all_config, dict)
        self.assertIn('theme', all_config)
        self.assertIn('font_size', all_config)
        self.assertIn('active_service', all_config)

    def test_invalid_json(self):
        """Test handling of invalid JSON file"""
        # Create invalid JSON file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")

        # Should load defaults without crashing
        controller = ConfigController(self.config_path)

        self.assertIsNotNone(controller.config)
        self.assertEqual(controller.config.theme, 'light')

    def test_json_encoding(self):
        """Test UTF-8 encoding in saved JSON"""
        controller = ConfigController(self.config_path)
        controller.save()

        # Verify file is UTF-8
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)

    def test_immediate_effect(self):
        """Test that set() has immediate effect"""
        controller = ConfigController(self.config_path)

        # Set multiple values
        controller.set('theme', 'dark')
        controller.set('font_size', 16)

        # Each set should save immediately
        # Load new controller to verify
        controller2 = ConfigController(self.config_path)

        self.assertEqual(controller2.config.theme, 'dark')
        self.assertEqual(controller2.config.font_size, 16)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
