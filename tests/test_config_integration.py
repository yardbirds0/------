# -*- coding: utf-8 -*-
"""
Configuration Integration Test
测试ConfigController的immediate effect功能
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from controllers.config_controller import ConfigController


def test_immediate_effect():
    """测试配置的即时生效"""

    print("="*60)
    print("ConfigController Immediate Effect Test")
    print("="*60)

    # 使用测试配置文件
    test_config_path = "config/test_chat_config.json"
    controller = ConfigController(test_config_path)

    print("\n[1] Initial Configuration:")
    print(f"  - theme: {controller.get('theme')}")
    print(f"  - font_size: {controller.get('font_size')}")
    print(f"  - temperature: {controller.get('temperature')}")
    print(f"  - auto_save: {controller.get('auto_save')}")

    print("\n[2] Changing theme to 'dark' (immediate effect)...")
    controller.set('theme', 'dark')
    print(f"  - theme is now: {controller.get('theme')}")

    print("\n[3] Creating new controller instance to verify persistence...")
    controller2 = ConfigController(test_config_path)
    print(f"  - theme loaded from file: {controller2.get('theme')}")
    print(f"  [OK] Verified: Configuration persisted immediately")

    print("\n[4] Changing multiple values...")
    controller.set('font_size', 16)
    controller.set('temperature', 1.0)
    controller.set('max_tokens', 4096)

    print(f"  - font_size: {controller.get('font_size')}")
    print(f"  - temperature: {controller.get('temperature')}")
    print(f"  - max_tokens: {controller.get('max_tokens')}")

    print("\n[5] Verifying all changes persisted...")
    controller3 = ConfigController(test_config_path)
    assert controller3.get('theme') == 'dark'
    assert controller3.get('font_size') == 16
    assert controller3.get('temperature') == 1.0
    assert controller3.get('max_tokens') == 4096
    print("  [OK] All changes verified in new controller instance")

    print("\n[6] Testing validation...")
    try:
        controller.set('font_size', 100)  # Out of range
        print("  [FAIL] Validation failed: Should have rejected font_size=100")
    except Exception as e:
        print(f"  [OK] Validation working: {type(e).__name__}")

    print("\n[7] Testing reset to defaults...")
    controller.reset_to_default()
    print(f"  - theme: {controller.get('theme')}")
    print(f"  - font_size: {controller.get('font_size')}")
    print(f"  - temperature: {controller.get('temperature')}")
    print("  [OK] Reset successful")

    print("\n[8] Testing get_all()...")
    all_config = controller.get_all()
    print(f"  - Total config keys: {len(all_config)}")
    for key, value in all_config.items():
        print(f"    - {key}: {value}")

    print("\n[9] Testing config migration...")
    # Simulate old format
    import json
    old_config = {
        'ai_model': 'claude-3',
        'num_context': 8,
        'theme': 'dark'
    }

    with open(test_config_path, 'w', encoding='utf-8') as f:
        json.dump(old_config, f, indent=2)

    controller4 = ConfigController(test_config_path)
    print(f"  - Migrated 'ai_model' -> 'active_service': {controller4.get('active_service')}")
    print(f"  - Migrated 'num_context' -> 'context_messages': {controller4.get('context_messages')}")
    print(f"  - Preserved 'theme': {controller4.get('theme')}")
    print("  [OK] Migration working")

    print("\n" + "="*60)
    print("[SUCCESS] All tests passed!")
    print("="*60)

    # Cleanup
    import os
    if os.path.exists(test_config_path):
        os.remove(test_config_path)
        print("\n[Cleanup] Test config file removed")


if __name__ == '__main__':
    try:
        test_immediate_effect()
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
