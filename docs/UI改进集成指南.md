# UI改进集成指南

## 概述

本文档说明如何将4个UI改进集成到现有系统中。

## ✅ 已完成的改进

### 1. 新建会话按钮优化
**文件**: `components/chat/widgets/session_list_panel.py`
- ✓ 按钮文字改为"新建会话"（4个中文字）
- ✓ 颜色改为绿色（#10B981正常，#059669悬停）
- ✓ 动态宽度自适应内容
- ✓ 水平居中对齐

**无需额外集成** - 已自动生效

---

### 2. 会话历史布局改进
**文件**: `components/chat/widgets/session_list_item.py`
- ✓ 标题和时间放在同一行
- ✓ 标题左对齐，时间右对齐
- ✓ 使用弹性空间分隔

**无需额外集成** - 已自动生效

---

### 3. 气泡复制功能
**文件**: `components/chat/widgets/message_bubble.py`
- ✓ 每个消息气泡下方添加复制按钮
- ✓ 鼠标悬停时淡入显示（200ms动画）
- ✓ 鼠标离开时淡出隐藏（200ms动画）
- ✓ 点击复制内容到剪贴板
- ✓ 复制成功显示"✓ 已复制"提示（2秒后恢复）

**无需额外集成** - MessageBubble组件已自动支持

---

### 4. AI气泡标题 ⚠️ 需要集成
**文件**: `components/chat/widgets/message_bubble.py`
- ✓ 左侧48x48紫色logo，显示🤖
- ✓ 右侧第一行：模型名称 | 提供商
- ✓ 右侧第二行：时间（月/日 时:分格式）

**⚠️ 需要修改调用代码** - 见下方集成步骤

---

## 🔧 集成步骤

### 步骤1：修改 `message_area.py`

需要修改3个地方的MessageBubble创建代码，添加AI消息的元数据参数。

#### 1.1 修改 `add_ai_message` 方法

**位置**: `components/chat/widgets/message_area.py` 第132-155行

**修改前**:
```python
def add_ai_message(self, content: str):
    """添加AI消息 (非流式)"""
    bubble = MessageBubble(content, is_user=False)
    # ...
```

**修改后**:
```python
def add_ai_message(
    self,
    content: str,
    model_name: str = None,
    provider: str = None,
    timestamp: str = None
):
    """
    添加AI消息 (非流式)

    Args:
        content: 消息内容
        model_name: AI模型名称
        provider: 提供商名称
        timestamp: 时间戳（格式：月/日 时:分，如"10/05 13:10"）
    """
    # 如果没有提供时间戳，使用当前时间
    if not timestamp:
        from datetime import datetime
        timestamp = datetime.now().strftime("%m/%d %H:%M")

    bubble = MessageBubble(
        content,
        is_user=False,
        model_name=model_name,
        provider=provider,
        timestamp=timestamp
    )
    # ... 其余代码不变
```

#### 1.2 修改 `update_streaming_message` 方法

**位置**: `components/chat/widgets/message_area.py` 第176-215行

在创建空气泡时添加元数据：

**修改前**:
```python
def update_streaming_message(self, chunk: str):
    """更新流式消息"""
    if self._current_streaming_bubble is None:
        # 创建空气泡
        bubble = MessageBubble("", is_user=False)
        # ...
```

**修改后**:
```python
def update_streaming_message(
    self,
    chunk: str,
    model_name: str = None,
    provider: str = None,
    timestamp: str = None
):
    """
    更新流式消息

    Args:
        chunk: 新的文本片段
        model_name: AI模型名称（仅在第一个chunk时使用）
        provider: 提供商名称（仅在第一个chunk时使用）
        timestamp: 时间戳（仅在第一个chunk时使用）
    """
    if self._current_streaming_bubble is None:
        # 如果没有提供时间戳，使用当前时间
        if not timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%m/%d %H:%M")

        # 创建空气泡（带元数据）
        bubble = MessageBubble(
            "",
            is_user=False,
            model_name=model_name,
            provider=provider,
            timestamp=timestamp
        )
        # ... 其余代码不变
```

---

### 步骤2：修改 `chat_controller.py`

需要从配置中获取模型信息，并传递给message_area。

#### 2.1 修改消息发送处理

**位置**: `controllers/chat_controller.py` 流式消息处理部分

找到调用 `update_streaming_message` 的地方，添加模型信息：

**示例修改**:
```python
def _on_chunk_received(self, chunk: str):
    """处理收到的数据块"""
    if self.chat_window:
        # 获取当前配置的模型信息
        model_name = self.current_config.model if self.current_config else None
        provider = self._get_provider_name()  # 需要添加此方法

        self.chat_window.message_area.update_streaming_message(
            chunk,
            model_name=model_name,
            provider=provider
        )

def _get_provider_name(self) -> str:
    """获取提供商名称"""
    if not self.current_config:
        return None

    # 根据API地址判断提供商
    api_url = self.current_config.api_url.lower()
    if 'openai' in api_url:
        return 'OpenAI'
    elif 'siliconflow' in api_url or 'silicon' in api_url:
        return '硅基流动'
    elif 'anthropic' in api_url:
        return 'Anthropic'
    else:
        return '自定义'
```

对于非流式消息，类似地修改调用：

```python
def _send_non_streaming_message(self, user_message: str):
    """发送非流式消息（示例）"""
    # ... AI响应处理 ...

    model_name = self.current_config.model if self.current_config else None
    provider = self._get_provider_name()

    self.chat_window.message_area.add_ai_message(
        ai_response,
        model_name=model_name,
        provider=provider
    )
```

---

## 🧪 测试

运行测试脚本验证所有功能：

```bash
# 测试会话列表改进（需求1、2）
python tests/test_ui_improvements.py
# 选择 1

# 测试消息气泡改进（需求3、4）
python tests/test_ui_improvements.py
# 选择 2
```

---

## 📋 检查清单

### 需求1：新建会话按钮 ✅
- [x] 文字改为"新建会话"
- [x] 颜色改为绿色
- [x] 动态宽度适配
- [x] 水平居中

### 需求2：会话历史布局 ✅
- [x] 标题和时间同行
- [x] 标题左对齐
- [x] 时间右对齐

### 需求3：气泡复制功能 ✅
- [x] 悬停显示复制按钮
- [x] 淡入淡出动画（200ms）
- [x] 复制到剪贴板
- [x] 复制成功提示

### 需求4：AI气泡标题 ✅
- [x] MessageBubble支持元数据参数
- [x] 48x48紫色logo显示🤖
- [x] 第一行显示"模型|提供商"
- [x] 第二行显示时间"月/日 时:分"
- [ ] ⚠️ 集成到message_area.py（待完成）
- [ ] ⚠️ 集成到chat_controller.py（待完成）

---

## 🚀 快速集成示例

如果您想快速看到AI气泡标题效果，可以在调用处直接传参：

```python
# 在任何创建AI消息的地方
from datetime import datetime

self.chat_window.message_area.add_ai_message(
    content="AI的回复内容",
    model_name="Qwen3-8B",
    provider="硅基流动",
    timestamp=datetime.now().strftime("%m/%d %H:%M")
)

# 或者对于流式消息（第一个chunk）
self.chat_window.message_area.update_streaming_message(
    chunk="第一个数据块",
    model_name="GPT-4",
    provider="OpenAI",
    timestamp=datetime.now().strftime("%m/%d %H:%M")
)
```

---

## ⚠️ 注意事项

1. **参数是可选的**: model_name、provider、timestamp都是可选参数，不传也不会报错，只是不显示标题
2. **时间格式**: 建议使用 `datetime.now().strftime("%m/%d %H:%M")` 格式化时间
3. **兼容性**: 所有改动向后兼容，不会影响现有代码
4. **流式消息**: 只需在第一个chunk时传递元数据，后续chunk会自动应用到同一个气泡

---

## 📞 支持

如有问题，请查看：
- `tests/test_ui_improvements.py` - 完整的测试示例
- `components/chat/widgets/message_bubble.py` - MessageBubble实现
- `components/chat/widgets/session_list_panel.py` - 会话列表实现
