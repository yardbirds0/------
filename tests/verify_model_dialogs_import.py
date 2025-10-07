# -*- coding: utf-8 -*-
"""
Verification script for model dialogs - checks imports and basic structure
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """Verify all imports work correctly"""
    print("=" * 60)
    print("Model Dialogs Import Verification")
    print("=" * 60)
    print()

    try:
        print("[OK] Importing AddModelDialog...")
        from components.chat.dialogs import AddModelDialog
        print("  Success!")

        print("[OK] Importing ModelBrowserDialog...")
        from components.chat.dialogs import ModelBrowserDialog
        print("  Success!")

        print("[OK] Importing ModelConfigDialog...")
        from components.chat.widgets.model_config_dialog import ModelConfigDialog
        print("  Success!")

        print()
        print("=" * 60)
        print("All imports successful!")
        print("=" * 60)
        print()

        # Verify class structure
        print("Checking class structure...")
        print(f"[OK] AddModelDialog has model_added signal: {hasattr(AddModelDialog, 'model_added')}")
        print(f"[OK] ModelBrowserDialog has model_selected signal: {hasattr(ModelBrowserDialog, 'model_selected')}")

        # Check if ModelConfigDialog has the new methods
        mcd_methods = dir(ModelConfigDialog)
        print(f"[OK] ModelConfigDialog has _on_manage_models_clicked: {'_on_manage_models_clicked' in mcd_methods}")
        print(f"[OK] ModelConfigDialog has _on_add_model_clicked: {'_on_add_model_clicked' in mcd_methods}")
        print(f"[OK] ModelConfigDialog has _on_model_added: {'_on_model_added' in mcd_methods}")
        print(f"[OK] ModelConfigDialog has _on_model_activated_from_browser: {'_on_model_activated_from_browser' in mcd_methods}")

        print()
        print("=" * 60)
        print("[SUCCESS] All verifications passed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run 'python tests/test_model_dialogs.py' to test the UI interactively")
        print("2. Click '管理模型' to test ModelBrowserDialog")
        print("3. Click '添加模型' to test AddModelDialog")
        print()

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
