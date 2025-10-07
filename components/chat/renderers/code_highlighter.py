# -*- coding: utf-8 -*-
"""
Code Highlighter
代码语法高亮器，使用Pygments提供多语言语法高亮
"""

from typing import Optional
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class CodeHighlighter:
    """
    代码语法高亮器
    使用Pygments对代码块进行语法高亮
    """

    def __init__(self):
        """初始化高亮器"""
        self.line_number_threshold = 10  # 超过此行数显示行号

    def highlight_code(self, code: str, language: Optional[str] = None, show_line_numbers: bool = None) -> str:
        """
        对代码进行语法高亮

        Args:
            code: 代码文本
            language: 语言名称（如'python', 'javascript'），None时自动检测
            show_line_numbers: 是否显示行号，None时根据代码行数自动判断

        Returns:
            str: 高亮后的HTML代码
        """
        if not PYGMENTS_AVAILABLE:
            # Pygments未安装，返回基础样式
            return self._basic_highlight(code)

        try:
            # 获取lexer
            if language:
                try:
                    lexer = get_lexer_by_name(language, stripall=True)
                except ClassNotFound:
                    # 语言不支持，尝试猜测
                    try:
                        lexer = guess_lexer(code)
                    except:
                        lexer = TextLexer()
            else:
                # 自动检测语言
                try:
                    lexer = guess_lexer(code)
                except:
                    lexer = TextLexer()

            # 确定是否显示行号
            if show_line_numbers is None:
                line_count = code.count('\n') + 1
                show_line_numbers = line_count > self.line_number_threshold

            # 创建formatter
            formatter = HtmlFormatter(
                style='github-dark',  # 使用GitHub Dark主题
                linenos='inline' if show_line_numbers else False,
                cssclass='cherry-code',
                wrapcode=True
            )

            # 生成高亮HTML
            highlighted_html = highlight(code, lexer, formatter)

            # 添加复制按钮
            html_with_copy = self._add_copy_button(highlighted_html, code)

            # 添加样式
            return self._add_styles(html_with_copy)

        except Exception as e:
            # 高亮失败，返回基础样式
            return self._basic_highlight(code)

    def _basic_highlight(self, code: str) -> str:
        """
        基础代码高亮（Pygments不可用时的降级方案）

        Args:
            code: 代码文本

        Returns:
            str: HTML代码块
        """
        escaped_code = self._escape_html(code)

        return f'''
        <div class="code-block">
            <div class="code-header">
                <button class="copy-button" onclick="copyCode(this)">📋 复制</button>
            </div>
            <pre><code>{escaped_code}</code></pre>
        </div>
        '''

    def _add_copy_button(self, html: str, code: str) -> str:
        """
        添加复制按钮到代码块

        Args:
            html: 原始HTML
            code: 原始代码（用于复制）

        Returns:
            str: 添加复制按钮后的HTML
        """
        # 转义代码用于data属性
        escaped_code = self._escape_html_attribute(code)

        # 在代码块开始处添加复制按钮
        copy_button = f'''
        <div class="code-header">
            <button class="copy-button" onclick="copyCode(this)" data-code="{escaped_code}">
                📋 复制
            </button>
        </div>
        '''

        # 将代码包装在容器中
        wrapped_html = f'<div class="code-block-container">{copy_button}{html}</div>'

        return wrapped_html

    def _add_styles(self, html: str) -> str:
        """
        添加Cherry Studio代码块样式

        Args:
            html: 原始HTML

        Returns:
            str: 添加样式后的HTML
        """
        styles = '''
        <style>
        .code-block-container {
            position: relative;
            margin: 1em 0;
            background-color: #1e1e1e;
            border: 1px solid #3e3e3e;
            border-radius: 8px;
            overflow: hidden;
        }

        .code-header {
            display: flex;
            justify-content: flex-end;
            padding: 8px 12px;
            background-color: #2d2d2d;
            border-bottom: 1px solid #3e3e3e;
        }

        .copy-button {
            background-color: #3B82F6;
            color: white;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .copy-button:hover {
            background-color: #2563EB;
        }

        .copy-button:active {
            background-color: #1D4ED8;
        }

        .cherry-code {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
            padding: 12px;
            margin: 0;
            background-color: #1e1e1e;
            color: #d4d4d4;
            overflow-x: auto;
        }

        .cherry-code .linenos {
            color: #858585;
            padding-right: 1em;
            user-select: none;
        }

        /* Pygments语法高亮颜色（GitHub Dark风格） */
        .cherry-code .k { color: #569cd6; }  /* Keyword */
        .cherry-code .kd { color: #569cd6; }  /* Keyword.Declaration */
        .cherry-code .kn { color: #c586c0; }  /* Keyword.Namespace */
        .cherry-code .kp { color: #569cd6; }  /* Keyword.Pseudo */
        .cherry-code .kr { color: #569cd6; }  /* Keyword.Reserved */
        .cherry-code .kt { color: #4ec9b0; }  /* Keyword.Type */

        .cherry-code .s { color: #ce9178; }  /* String */
        .cherry-code .s1 { color: #ce9178; }  /* String.Single */
        .cherry-code .s2 { color: #ce9178; }  /* String.Double */
        .cherry-code .sb { color: #ce9178; }  /* String.Backtick */

        .cherry-code .m { color: #b5cea8; }  /* Number */
        .cherry-code .mi { color: #b5cea8; }  /* Number.Integer */
        .cherry-code .mf { color: #b5cea8; }  /* Number.Float */

        .cherry-code .c { color: #6a9955; }  /* Comment */
        .cherry-code .c1 { color: #6a9955; }  /* Comment.Single */
        .cherry-code .cm { color: #6a9955; }  /* Comment.Multiline */

        .cherry-code .nf { color: #dcdcaa; }  /* Name.Function */
        .cherry-code .nc { color: #4ec9b0; }  /* Name.Class */
        .cherry-code .nn { color: #4ec9b0; }  /* Name.Namespace */

        .cherry-code .o { color: #d4d4d4; }  /* Operator */
        .cherry-code .p { color: #d4d4d4; }  /* Punctuation */
        </style>

        <script>
        function copyCode(button) {
            const code = button.getAttribute('data-code');
            if (!code) return;

            // 解码HTML实体
            const temp = document.createElement('textarea');
            temp.innerHTML = code;
            const decodedCode = temp.value;

            // 复制到剪贴板
            navigator.clipboard.writeText(decodedCode).then(() => {
                // 显示反馈
                const originalText = button.textContent;
                button.textContent = '✓ 已复制';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            }).catch(err => {
                console.error('复制失败:', err);
                button.textContent = '✗ 复制失败';
                setTimeout(() => {
                    button.textContent = '📋 复制';
                }, 2000);
            });
        }
        </script>
        '''

        return styles + html

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

    @staticmethod
    def _escape_html_attribute(text: str) -> str:
        """
        转义HTML属性值

        Args:
            text: 原始文本

        Returns:
            str: 转义后可安全用于HTML属性的文本
        """
        return (text
                .replace('&', '&amp;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\n', '&#10;'))


# ==================== 测试代码 ====================

if __name__ == "__main__":
    highlighter = CodeHighlighter()

    # 测试Python代码
    python_code = '''def fibonacci(n):
    """计算斐波那契数列第n项"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 测试调用
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")'''

    print("=== Python代码高亮测试 ===")
    html = highlighter.highlight_code(python_code, 'python')
    print(html[:500])  # 打印前500字符

    # 测试JavaScript代码
    js_code = '''function factorial(n) {
    if (n === 0 || n === 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

console.log("5! =", factorial(5));'''

    print("\n=== JavaScript代码高亮测试 ===")
    html = highlighter.highlight_code(js_code, 'javascript')
    print(html[:500])  # 打印前500字符

    print("\n=== 测试完成 ===")
