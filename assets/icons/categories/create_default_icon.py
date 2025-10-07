#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认分类图标占位符
运行此脚本会创建一个简单的default.png图标
"""

from pathlib import Path

def create_default_icon():
    """创建一个简单的24×24px默认分类图标"""
    try:
        from PIL import Image, ImageDraw

        # 创建24×24的图像，RGBA模式（支持透明）
        img = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制一个圆形背景
        draw.ellipse([2, 2, 22, 22], fill='#10B981', outline='#059669', width=2)

        # 绘制简化的分类图标（三条横线代表列表/分类）
        # 顶部横线
        draw.rectangle([7, 8, 17, 9], fill='white')
        # 中间横线
        draw.rectangle([7, 12, 17, 13], fill='white')
        # 底部横线
        draw.rectangle([7, 16, 17, 17], fill='white')

        # 保存图标
        output_path = Path(__file__).parent / 'default.png'
        img.save(output_path, 'PNG')
        print(f"[OK] Default category icon created: {output_path}")

        return True

    except ImportError:
        print("[ERROR] Need to install Pillow: pip install Pillow")
        print("Or manually create a 24x24 default.png icon file")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create icon: {e}")
        return False


if __name__ == "__main__":
    create_default_icon()
