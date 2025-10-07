# -*- coding: utf-8 -*-
"""
TitleBarModelIndicator - Compact widget displaying current AI model in title bar
Shows: [Icon] ModelName | ProviderName ◇
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor, QPainter, QPalette
from pathlib import Path

from ..controllers.config_controller import ConfigController


class TitleBarModelIndicator(QWidget):
    """
    Title bar model indicator widget

    Displays current model and provider in a compact format.
    Clickable to open model configuration dialog.

    Size: 200×32px (height fixed, width adapts to content)
    Layout: [Icon(24px)] [ModelName] | [ProviderName] [Arrow(12px)]

    Signals:
        clicked: Emitted when widget is clicked
    """

    # Signals
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configuration controller
        self.config_controller = ConfigController.instance()

        # Widget state
        self._provider_id = ""
        self._model_id = ""
        self._provider_name = ""
        self._model_name = ""
        self._icon_path = ""

        # UI elements
        self.icon_label: Optional[QLabel] = None
        self.model_label: Optional[QLabel] = None
        self.separator_label: Optional[QLabel] = None
        self.provider_label: Optional[QLabel] = None
        self.arrow_label: Optional[QLabel] = None

        self._setup_ui()
        self._connect_signals()
        self._update_from_config()

    def _setup_ui(self):
        """Setup UI components"""
        # Widget properties
        self.setFixedHeight(32)
        self.setMaximumWidth(500)  # 增加到500px以显示长模型名称
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setScaledContents(True)
        layout.addWidget(self.icon_label)

        # Model name label
        self.model_label = QLabel("--")
        self.model_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #10B981;
            }
        """)
        layout.addWidget(self.model_label)

        # Separator
        self.separator_label = QLabel("|")
        self.separator_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666;
            }
        """)
        layout.addWidget(self.separator_label)

        # Provider name label
        self.provider_label = QLabel("--")
        self.provider_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 400;
                color: #3B82F6;
            }
        """)
        layout.addWidget(self.provider_label)

        # Dropdown arrow
        self.arrow_label = QLabel("◇")
        self.arrow_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #9AA0A6;
            }
        """)
        layout.addWidget(self.arrow_label)

        # Widget styling
        self.setStyleSheet("""
            TitleBarModelIndicator {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
            TitleBarModelIndicator:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

    def _connect_signals(self):
        """Connect to ConfigController signals"""
        self.config_controller.model_changed.connect(self._on_model_changed)
        self.config_controller.config_loaded.connect(self._update_from_config)

    def _update_from_config(self):
        """Update display from current configuration"""
        # Get current model
        provider_id, model_id = self.config_controller.get_current_model()

        # Update internal state
        self._provider_id = provider_id
        self._model_id = model_id

        if not provider_id or not model_id:
            # No model configured
            self._show_unconfigured()
            return

        # Get provider details
        provider = self.config_controller.get_provider(provider_id)
        if not provider:
            self._show_unconfigured()
            return

        self._provider_name = provider.get("name", "Unknown")

        # Get model details
        models = provider.get("models", [])
        model = next((m for m in models if m.get("id") == model_id), None)
        if not model:
            self._model_name = model_id  # Fallback to ID
        else:
            self._model_name = model.get("name", model_id)

        # Get icon path
        icon_filename = provider.get("icon", "default.png")
        self._icon_path = f"assets/icons/providers/{icon_filename}"

        # Update UI
        self._update_display()

    def _show_unconfigured(self):
        """Show unconfigured state"""
        self._model_name = "未配置模型"
        self._provider_name = ""
        self._icon_path = "assets/icons/providers/default.png"

        # Update display with warning color
        self.model_label.setText(self._model_name)
        self.model_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #FFA500;
            }
        """)
        self.provider_label.setText("")
        self.separator_label.setVisible(False)

        # Load default icon
        self._load_icon(self._icon_path)

    def _update_display(self):
        """Update visual display"""
        # Truncate model name if too long (增加到60个字符)
        display_name = self._truncate_text(self._model_name, 60)

        # Update labels
        self.model_label.setText(display_name)
        self.provider_label.setText(self._provider_name)
        self.separator_label.setVisible(True)

        # Restore normal styling
        self.model_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #10B981;
            }
        """)

        # Set tooltip with full name if truncated
        if display_name != self._model_name:
            self.model_label.setToolTip(self._model_name)
        else:
            self.model_label.setToolTip("")

        # Load icon
        self._load_icon(self._icon_path)

    def _load_icon(self, icon_path: str):
        """
        Load provider icon from file

        Args:
            icon_path: Path to icon file
        """
        path = Path(icon_path)

        # Try to load icon
        if path.exists():
            pixmap = QPixmap(str(path))
        else:
            # Fallback to default icon
            default_path = Path("assets/icons/providers/default.png")
            if default_path.exists():
                pixmap = QPixmap(str(default_path))
            else:
                # Create simple placeholder pixmap
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.gray)

        # Set scaled pixmap
        self.icon_label.setPixmap(pixmap)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text with ellipsis if exceeds max length

        Args:
            text: Text to truncate
            max_length: Maximum character length

        Returns:
            Truncated text with ... if needed
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _on_model_changed(self, provider_id: str, model_id: str):
        """
        Handle model change signal

        Args:
            provider_id: New provider ID
            model_id: New model ID
        """
        self._update_from_config()

    def mousePressEvent(self, event):
        """
        Handle mouse press event

        Emits clicked signal when widget is clicked.
        """
        if event.button() == Qt.LeftButton:
            # Check if request is active
            if self.config_controller.request_active:
                # Don't allow click during active request
                event.ignore()
                return

            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter event"""
        # Show hover effect (handled by stylesheet)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave event"""
        # Remove hover effect (handled by stylesheet)
        super().leaveEvent(event)
