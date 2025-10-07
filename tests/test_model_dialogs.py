# -*- coding: utf-8 -*-
"""
Test script for model dialogs (AddModelDialog and ModelBrowserDialog)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.widgets.model_config_dialog import ModelConfigDialog


def test_model_dialogs():
    """Test the model dialogs integration"""
    app = QApplication(sys.argv)

    # Create and show ModelConfigDialog
    dialog = ModelConfigDialog()

    print("=" * 60)
    print("Model Dialogs Test")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Click '管理模型' button to open ModelBrowserDialog")
    print("   - Test search functionality")
    print("   - Test category filtering")
    print("   - Click on a model to select it")
    print()
    print("2. Click '添加模型' button to open AddModelDialog")
    print("   - Enter Model ID (required)")
    print("   - Enter Model Name (optional)")
    print("   - Enter Group Name (optional)")
    print("   - Click '添加模型' to add")
    print()
    print("3. Verify:")
    print("   - Both dialogs open correctly")
    print("   - UI matches the reference PNG designs")
    print("   - Cherry theme styling is applied")
    print("   - Model selection/addition works")
    print()
    print("=" * 60)

    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_model_dialogs()
