# -*- coding: utf-8 -*-
"""
Unit tests for TitleBarModelIndicator widget
"""

import pytest
from unittest.mock import MagicMock, Mock
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtTest import QTest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.chat.widgets.title_bar_model_indicator import TitleBarModelIndicator
from components.chat.controllers.config_controller import ConfigController


# Create QCoreApplication instance
app = QCoreApplication.instance() or QCoreApplication(sys.argv)


@pytest.fixture
def config_controller():
    """Setup ConfigController singleton"""
    # Reset singleton
    ConfigController._instance = None
    controller = ConfigController.instance()
    yield controller
    # Reset after test
    ConfigController._instance = None


@pytest.fixture
def indicator(config_controller):
    """Create TitleBarModelIndicator instance"""
    widget = TitleBarModelIndicator()
    yield widget
    widget.deleteLater()


class TestTitleBarModelIndicatorCreation:
    """Test widget creation and initialization"""

    def test_widget_created(self, indicator):
        """Test that widget is created successfully"""
        assert indicator is not None
        assert isinstance(indicator, TitleBarModelIndicator)

    def test_widget_size(self, indicator):
        """Test widget size constraints"""
        assert indicator.height() == 32
        assert indicator.maximumWidth() == 200

    def test_cursor_is_pointer(self, indicator):
        """Test that cursor changes to pointer"""
        assert indicator.cursor().shape() == Qt.PointingHandCursor


class TestDisplayUpdates:
    """Test display update functionality"""

    def test_displays_default_model(self, indicator, config_controller):
        """Test that default model is displayed"""
        # Get default model
        provider_id, model_id = config_controller.get_current_model()

        # Trigger update
        indicator._update_from_config()

        # Verify display updated
        assert indicator.model_label.text() != "--"
        assert indicator.provider_label.text() != "--"

    def test_displays_model_after_change(self, indicator, config_controller):
        """Test that display updates after model change"""
        # Change model
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Wait for signal
        QTest.qWait(100)

        # Verify display updated
        assert "GPT-4" in indicator.model_label.text()
        assert "OpenAI" in indicator.provider_label.text()

    def test_shows_unconfigured_warning(self, indicator, config_controller):
        """Test unconfigured state display"""
        # Set empty current model
        config_controller.config["current_provider"] = ""
        config_controller.config["current_model"] = ""

        # Update display
        indicator._update_from_config()

        # Verify warning shown
        assert "未配置" in indicator.model_label.text()

    def test_text_truncation(self, indicator):
        """Test text truncation for long model names"""
        long_text = "Very Long Model Name That Should Be Truncated"
        truncated = indicator._truncate_text(long_text, 15)

        assert len(truncated) <= 15
        assert truncated.endswith("...")


class TestSignalConnections:
    """Test signal connections and emission"""

    def test_clicked_signal_emitted(self, indicator):
        """Test that clicked signal is emitted on mouse press"""
        # Connect signal spy
        signal_spy = MagicMock()
        indicator.clicked.connect(signal_spy)

        # Simulate left mouse click
        QTest.mouseClick(indicator, Qt.LeftButton)

        # Verify signal emitted
        signal_spy.assert_called_once()

    def test_model_changed_signal_updates_display(self, indicator, config_controller):
        """Test that model_changed signal triggers display update"""
        # Connect signal spy to verify update
        original_text = indicator.model_label.text()

        # Change model
        config_controller.set_current_model("openai", "gpt-4-turbo")

        # Wait for signal
        QTest.qWait(100)

        # Verify display changed
        assert indicator.model_label.text() != original_text

    def test_click_disabled_during_request(self, indicator, config_controller):
        """Test that click is ignored during active request"""
        # Set request active
        config_controller.set_request_active(True)

        # Try to click
        signal_spy = MagicMock()
        indicator.clicked.connect(signal_spy)

        QTest.mouseClick(indicator, Qt.LeftButton)

        # Verify signal NOT emitted
        signal_spy.assert_not_called()

        # Set request inactive
        config_controller.set_request_active(False)


class TestIconLoading:
    """Test icon loading functionality"""

    def test_loads_icon(self, indicator):
        """Test that icon is loaded"""
        # Update display
        indicator._update_from_config()

        # Verify icon label has pixmap
        assert indicator.icon_label.pixmap() is not None

    def test_fallback_icon_on_missing_file(self, indicator):
        """Test fallback to default icon when file missing"""
        # Try to load non-existent icon
        indicator._load_icon("nonexistent/path.png")

        # Verify icon still loaded (default or placeholder)
        assert indicator.icon_label.pixmap() is not None


class TestTooltip:
    """Test tooltip functionality"""

    def test_tooltip_shown_for_truncated_text(self, indicator):
        """Test that tooltip shows full text when truncated"""
        # Set long model name
        long_name = "Very Long Model Name That Will Be Truncated"
        indicator._model_name = long_name

        # Update display (triggers truncation)
        indicator._update_display()

        # Verify tooltip set
        if indicator.model_label.text() != long_name:
            assert indicator.model_label.toolTip() == long_name

    def test_no_tooltip_for_short_text(self, indicator):
        """Test that no tooltip for short text"""
        # Set short model name
        short_name = "GPT-4"
        indicator._model_name = short_name

        # Update display
        indicator._update_display()

        # Verify no tooltip
        assert indicator.model_label.toolTip() == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
