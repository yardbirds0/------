# -*- coding: utf-8 -*-
"""
Markdown Renderer
将 Markdown 文本转换为 HTML，支持代码高亮和格式化
"""

import re
from typing import Optional
try:
    import markdown
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class MarkdownRenderer:
    """
    Markdown 渲染器
    将 Markdown 文本转换为可在 Qt 中显示的 HTML
    """

    def __init__(self):
        """初始化渲染器"""
        self.formatter = HtmlFormatter(style='monokai', noclasses=True) if MARKDOWN_AVAILABLE else None

    def render(self, markdown_text: str) -> str:
        """
        渲染 Markdown 为 HTML

        Args:
            markdown_text: Markdown 格式文本

        Returns:
            HTML 字符串
        """
        if not MARKDOWN_AVAILABLE:
            # 降级处理：简单替换换行符
            return f"<p>{self._escape_html(markdown_text).replace(chr(10), '<br>')}</p>"

        try:
            # 预处理代码块（添加语法高亮）
            markdown_text = self._highlight_code_blocks(markdown_text)

            # 转换 Markdown 为 HTML
            html = markdown.markdown(
                markdown_text,
                extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
            )

            # 添加样式
            html = self._add_styles(html)

            return html

        except Exception as e:
            # 渲染失败时返回纯文本
            return f"<p>[渲染错误] {self._escape_html(str(e))}</p><pre>{self._escape_html(markdown_text)}</pre>"

    def _highlight_code_blocks(self, text: str) -> str:
        """
        为代码块添加语法高亮

        Args:
            text: 包含代码块的 Markdown 文本

        Returns:
            处理后的文本
        """
        if not MARKDOWN_AVAILABLE:
            return text

        # 正则匹配代码块：```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)\n```'

        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)

            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except:
                try:
                    lexer = guess_lexer(code)
                except:
                    # 无法识别语言，使用纯文本
                    return f"<pre><code>{self._escape_html(code)}</code></pre>"

            # 高亮代码
            highlighted = highlight(code, lexer, self.formatter)
            return highlighted

        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)

    def _add_styles(self, html: str) -> str:
        """
        为 HTML 添加样式

        Args:
            html: HTML 字符串

        Returns:
            带样式的 HTML
        """
        # 添加基础样式
        styled_html = f"""
        <div style="font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6;">
            {html}
        </div>
        """
        return styled_html

    def _escape_html(self, text: str) -> str:
        """
        转义 HTML 特殊字符

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# 全局渲染器实例
_renderer = MarkdownRenderer()


def render_markdown(text: str) -> str:
    """
    快捷函数：渲染 Markdown 文本

    Args:
        text: Markdown 文本

    Returns:
        HTML 字符串
    """
    return _renderer.render(text)
