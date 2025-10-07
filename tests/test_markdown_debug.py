# -*- coding: utf-8 -*-
"""
调试Markdown渲染器输出
"""

import sys
from pathlib import Path
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.renderers import MarkdownRenderer

# 测试Markdown渲染
renderer = MarkdownRenderer()

markdown_text = """
# 一级标题

这是一段**粗体文字**和*斜体文字*。

## 二级标题

```python
def hello():
    print("Hello World")
```
"""

html = renderer.render(markdown_text)

print("=" * 60)
print("Markdown输入:")
print("=" * 60)
print(markdown_text)

print("\n" + "=" * 60)
print("完整HTML输出:")
print("=" * 60)
print(html)

print("\n" + "=" * 60)
print("检查关键标签:")
print("=" * 60)

checks = {
    '<h1>': '<h1>' in html,
    '<h2>': '<h2>' in html,
    '<h1 id=': '<h1 id=' in html,
    '<h2 id=': '<h2 id=' in html,
    '<strong>': '<strong>' in html,
    '<em>': '<em>' in html,
    '<code>': '<code>' in html,
    '<pre>': '<pre>' in html,
    'cherry-code': 'cherry-code' in html,
    'cherry-markdown': 'cherry-markdown' in html,
}

for tag, found in checks.items():
    status = "✓" if found else "✗"
    print(f"{status} {tag}: {found}")
