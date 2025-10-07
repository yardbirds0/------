# -*- coding: utf-8 -*-
"""
Markdown Renderer
Markdown到HTML渲染器，支持代码高亮和流式输出
"""

import re
from typing import Optional
import markdown2
from .code_highlighter import CodeHighlighter


class MarkdownRenderer:
    """
    Markdown渲染器
    支持完整Markdown语法、代码高亮和增量渲染
    """

    def __init__(self):
        """初始化渲染器"""
        # Markdown2扩展配置
        self.extras = [
            'fenced-code-blocks',  # 围栏代码块 ```language
            'tables',              # 表格支持
            'strike',              # 删除线 ~~text~~
            'task_list',           # 任务列表 - [ ] / - [x]
            'header-ids',          # 标题ID
            'code-friendly',       # 代码友好
            'cuddled-lists',       # 紧凑列表
            'markdown-in-html',    # HTML中的Markdown
        ]

        # 流式渲染缓冲区
        self.streaming_buffer = ""
        self.last_rendered_html = ""

        # 代码高亮器
        self.code_highlighter = CodeHighlighter()

    def render(self, text: str) -> str:
        """
        将Markdown文本渲染为HTML

        Args:
            text: Markdown文本

        Returns:
            str: 渲染后的HTML
        """
        if not text:
            return ""

        try:
            # 使用markdown2渲染
            html = markdown2.markdown(text, extras=self.extras)

            # 后处理：应用代码高亮
            html = self._apply_code_highlighting(html)

            # 应用Cherry Studio样式
            html = self._apply_cherry_styles(html)

            return html

        except Exception as e:
            # 渲染失败时返回纯文本
            return f'<pre>{self._escape_html(text)}</pre>'

    def render_incremental(self, chunk: str) -> str:
        """
        增量渲染（用于流式输出）

        Args:
            chunk: 新增的文本片段

        Returns:
            str: 新增部分的HTML（相对于上次渲染）
        """
        # 添加到缓冲区
        self.streaming_buffer += chunk

        # 检测是否有完整的块（段落、代码块等）
        if self._has_complete_block(self.streaming_buffer):
            # 渲染整个缓冲区
            current_html = self.render(self.streaming_buffer)

            # 计算新增的HTML（简化实现：返回全部）
            # TODO: 实现真正的增量diff
            new_html = current_html

            self.last_rendered_html = current_html
            return new_html
        else:
            # 块不完整，暂不渲染
            # 返回简单的文本显示
            return f'<span class="streaming-text">{self._escape_html(chunk)}</span>'

    def reset_streaming(self):
        """重置流式渲染状态"""
        self.streaming_buffer = ""
        self.last_rendered_html = ""

    def _apply_code_highlighting(self, html: str) -> str:
        """
        对HTML中的代码块应用语法高亮

        Args:
            html: Markdown2渲染后的HTML

        Returns:
            str: 应用高亮后的HTML
        """
        # 匹配 <pre><code class="language-xxx">...</code></pre> 或 <pre><code>...</code></pre>
        pattern = r'<pre><code(?:\s+class="([^"]*)")?>(.*?)</code></pre>'

        def replace_code_block(match):
            class_attr = match.group(1) or ""
            code_content = match.group(2)

            # 解码HTML实体
            code_content = (code_content
                           .replace('&lt;', '<')
                           .replace('&gt;', '>')
                           .replace('&amp;', '&')
                           .replace('&quot;', '"')
                           .replace('&#39;', "'"))

            # 提取语言名（如 "language-python" -> "python"）
            language = None
            if class_attr:
                if class_attr.startswith('language-'):
                    language = class_attr[9:]  # 去掉"language-"前缀
                else:
                    language = class_attr

            # 使用CodeHighlighter进行高亮
            return self.code_highlighter.highlight_code(code_content, language)

        # 替换所有代码块
        return re.sub(pattern, replace_code_block, html, flags=re.DOTALL)

    def _has_complete_block(self, text: str) -> bool:
        """
        检测是否包含完整的块

        Args:
            text: 文本内容

        Returns:
            bool: 是否包含完整块
        """
        # 简单实现：检查是否以双换行符结束（段落结束）
        # 或者包含完整的代码块
        if text.endswith('\n\n'):
            return True

        # 检测完整的代码块
        if '```' in text:
            count = text.count('```')
            # 代码块成对出现
            if count >= 2 and count % 2 == 0:
                return True

        return False

    def _apply_cherry_styles(self, html: str) -> str:
        """
        应用Cherry Studio样式

        Args:
            html: 原始HTML

        Returns:
            str: 应用样式后的HTML
        """
        # 包裹在styled div中
        styled_html = f'<div class="cherry-markdown">{html}</div>'

        # 添加样式标签
        style = '''
        <style>
        .cherry-markdown {
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #1F2937;
        }

        .cherry-markdown h1, .cherry-markdown h2, .cherry-markdown h3 {
            color: #1F2937;
            font-weight: 600;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }

        .cherry-markdown h1 { font-size: 1.8em; }
        .cherry-markdown h2 { font-size: 1.5em; }
        .cherry-markdown h3 { font-size: 1.25em; }

        .cherry-markdown p {
            margin: 0.8em 0;
        }

        .cherry-markdown code {
            background-color: #F3F4F6;
            color: #EF4444;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }

        .cherry-markdown pre {
            background-color: #F3F4F6;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 12px;
            overflow-x: auto;
            margin: 1em 0;
        }

        .cherry-markdown pre code {
            background: none;
            color: #1F2937;
            padding: 0;
        }

        .cherry-markdown table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }

        .cherry-markdown th, .cherry-markdown td {
            border: 1px solid #E5E7EB;
            padding: 8px 12px;
            text-align: left;
        }

        .cherry-markdown th {
            background-color: #F7F8FA;
            font-weight: 600;
        }

        .cherry-markdown ul, .cherry-markdown ol {
            padding-left: 2em;
            margin: 0.8em 0;
        }

        .cherry-markdown li {
            margin: 0.3em 0;
        }

        .cherry-markdown blockquote {
            border-left: 4px solid #3B82F6;
            padding-left: 1em;
            margin: 1em 0;
            color: #6B7280;
            font-style: italic;
        }

        .cherry-markdown a {
            color: #3B82F6;
            text-decoration: none;
        }

        .cherry-markdown a:hover {
            text-decoration: underline;
        }

        .streaming-text {
            color: #6B7280;
            animation: pulse 1.5s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        </style>
        '''

        return style + styled_html

    @staticmethod
    def _escape_html(text: str) -> str:
        """
        转义HTML特殊字符

        Args:
            text: 原始文本

        Returns:
            str: 转义后的文本
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 测试Markdown渲染
    renderer = MarkdownRenderer()

    # 测试文本
    markdown_text = """
# 标题示例

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

## 列表示例

- 无序列表项1
- 无序列表项2
  - 嵌套项

1. 有序列表项1
2. 有序列表项2

## 表格示例

| 项目 | 值 |
|------|------|
| Temperature | 0.7 |
| Max Tokens | 2048 |

## 任务列表

- [x] 已完成任务
- [ ] 待办任务

> 这是一段引用文字
"""

    html = renderer.render(markdown_text)
    print(html)
    print("\n=== 测试完成 ===")
