#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认图标占位符
运行此脚本会创建一个简单的default.png图标
"""

from pathlib import Path

def create_default_icon():
    """创建一个简单的24×24px默认图标"""
    try:
        from PIL import Image, ImageDraw

        # 创建24×24的图像，RGBA模式（支持透明）
        img = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制一个圆形背景
        draw.ellipse([2, 2, 22, 22], fill='#3B82F6', outline='#2563EB', width=2)

        # 绘制字母 "AI"
        # 由于PIL的文字渲染需要字体文件，这里用简单的形状代替
        # 绘制一个简化的AI图标（三角形+圆形）
        draw.polygon([(8, 14), (12, 8), (16, 14)], fill='white')
        draw.ellipse([10, 16, 14, 20], fill='white')

        # 保存图标
        output_path = Path(__file__).parent / 'default.png'
        img.save(output_path, 'PNG')
        print(f"[OK] Default icon created: {output_path}")

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
