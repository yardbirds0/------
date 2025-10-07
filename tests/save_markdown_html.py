# -*- coding: utf-8 -*-
"""
保存Markdown渲染HTML到文件
"""

import sys
from pathlib import Path

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

# 保存到文件
output_file = Path(__file__).parent / "markdown_output.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML已保存到: {output_file}")
print(f"文件大小: {len(html)} 字符")
