# -*- coding: utf-8 -*-
"""
测试Markdown渲染功能
验证MessageBubble组件的Markdown渲染和代码高亮功能
"""

import sys
from pathlib import Path
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.renderers import MarkdownRenderer, CodeHighlighter


def test_markdown_renderer():
    """测试Markdown渲染器"""
    print("=" * 60)
    print("测试 Markdown 渲染器")
    print("=" * 60)

    renderer = MarkdownRenderer()

    # 测试文本
    markdown_text = """
# 标题测试

这是一段**粗体文字**和*斜体文字*。

## 代码示例

行内代码：`print("Hello World")`

代码块：
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## 列表测试

- 项目1
- 项目2
  - 子项目

## 表格测试

| 参数 | 值 |
|------|------|
| Temperature | 0.7 |
| Max Tokens | 2048 |
"""

    try:
        html = renderer.render(markdown_text)

        # 检查是否包含关键HTML标签
        checks = [
            ('<h1' in html and 'id=' in html, "H1标题"),  # markdown2使用header-ids扩展
            ('<h2' in html and 'id=' in html, "H2标题"),
            ('<strong>' in html or '<b>' in html, "粗体"),
            ('<em>' in html or '<i>' in html, "斜体"),
            ('<code>' in html, "代码块"),
            ('<ul>' in html or '<ol>' in html, "列表"),
            ('<table>' in html, "表格"),
            ('class="cherry-markdown"' in html, "Cherry样式"),
        ]

        print("\n✓ Markdown渲染测试:")
        for check, name in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {name}: {'通过' if check else '失败'}")

        all_passed = all(check for check, _ in checks)
        print(f"\n{'✓' if all_passed else '✗'} Markdown渲染器测试: {'全部通过' if all_passed else '部分失败'}")

        return all_passed

    except Exception as e:
        print(f"\n✗ Markdown渲染器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_highlighter():
    """测试代码高亮器"""
    print("\n" + "=" * 60)
    print("测试 代码高亮器")
    print("=" * 60)

    highlighter = CodeHighlighter()

    # 测试Python代码
    python_code = '''def fibonacci(n):
    """计算斐波那契数列第n项"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''

    try:
        html = highlighter.highlight_code(python_code, 'python')

        # 检查是否包含关键元素
        checks = [
            ('<pre>' in html or '<code>' in html, "代码块标签"),
            ('copy-button' in html, "复制按钮"),
            ('class=' in html, "CSS类"),
            ('<style>' in html, "样式表"),
            ('function copyCode' in html, "复制功能"),
        ]

        print("\n✓ 代码高亮测试:")
        for check, name in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {name}: {'通过' if check else '失败'}")

        all_passed = all(check for check, _ in checks)
        print(f"\n{'✓' if all_passed else '✗'} 代码高亮器测试: {'全部通过' if all_passed else '部分失败'}")

        return all_passed

    except Exception as e:
        print(f"\n✗ 代码高亮器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """测试集成功能"""
    print("\n" + "=" * 60)
    print("测试 Markdown + 代码高亮集成")
    print("=" * 60)

    renderer = MarkdownRenderer()

    markdown_with_code = """
# 函数示例

这是一个Python函数示例：

```python
def greet(name):
    return f"Hello, {name}!"
```

这是一个JavaScript示例：

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}
```
"""

    try:
        html = renderer.render(markdown_with_code)

        # 检查集成是否正常
        checks = [
            ('<h1' in html, "Markdown标题"),  # 标题存在
            ('<code>' in html or 'codehilite' in html, "代码高亮"),  # 代码高亮(Pygments)
            ('<span class=' in html, "语法高亮标记"),  # Pygments语法高亮
            ('cherry-markdown' in html, "Markdown样式"),
        ]

        print("\n✓ 集成测试:")
        for check, name in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {name}: {'通过' if check else '失败'}")

        all_passed = all(check for check, _ in checks)
        print(f"\n{'✓' if all_passed else '✗'} 集成测试: {'全部通过' if all_passed else '部分失败'}")

        return all_passed

    except Exception as e:
        print(f"\n✗ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("开始测试 US-1.2: Markdown渲染引擎")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("Markdown渲染器", test_markdown_renderer()))
    results.append(("代码高亮器", test_code_highlighter()))
    results.append(("集成测试", test_integration()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, passed in results:
        status = "✓" if passed else "✗"
        print(f"{status} {name}: {'通过' if passed else '失败'}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过! US-1.2 功能验证成功!")
    else:
        print("✗ 部分测试失败，请检查相关功能")
    print("=" * 60)
