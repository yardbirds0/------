# -*- coding: utf-8 -*-
"""
Test script for redesigned ModelBrowserDialog
Verifies the new category-based layout with edit/delete functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from components.chat.dialogs.model_browser_dialog import ModelBrowserDialog


class TestWindow(QMainWindow):
    """Test window for ModelBrowserDialog"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Model Browser Redesign")
        self.resize(400, 300)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Test button
        test_btn = QPushButton("Open Model Browser (Redesigned)")
        test_btn.setFixedSize(300, 50)
        test_btn.clicked.connect(self.open_browser)
        layout.addWidget(test_btn)

        layout.addStretch()

    def open_browser(self):
        """Open ModelBrowserDialog"""
        dialog = ModelBrowserDialog(self)
        dialog.exec()


def main():
    """Main test function"""
    app = QApplication(sys.argv)

    print("=" * 60)
    print("ModelBrowserDialog Redesign Test")
    print("=" * 60)
    print("\nTest Features:")
    print("1. Category blocks with gray headers")
    print("2. Model rows with category icons")
    print("3. Edit button (gear icon) - Opens AddModelDialog pre-filled")
    print("4. Delete button (-) - Removes model from configuration")
    print("5. White background with clean design")
    print("6. No '[内置]' or '[自定义]' labels")
    print("\nIcon Placement:")
    print("- Category icons: assets/icons/categories/")
    print("  - Format: {category-name}.png (e.g., gemini.png, gpt-4.png)")
    print("  - Fallback: default.png (green circle with lines)")
    print("\nClick the button to test the redesigned dialog.")
    print("=" * 60)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
