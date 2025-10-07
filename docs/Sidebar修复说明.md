# Sidebar修复说明

## 问题描述

在删除Icon导航栏后，主程序启动失败，报错：
```
'CherrySidebar' object has no attribute 'new_chat_requested'
```

## 根本原因

删除Icon导航栏时，我移除了`new_chat_requested`和`manage_chats_requested`信号定义，但`main_window.py`中还在使用这些信号：

```python
# components/chat/main_window.py, line 122-123
self.sidebar.new_chat_requested.connect(self._on_new_tab)
self.sidebar.manage_chats_requested.connect(self._on_manage_chats)
```

## 解决方案

### 1. 保留兼容性信号

在`sidebar.py`中重新添加这两个信号，作为兼容性信号：

```python
# 会话相关信号（新）
session_selected = Signal(str)  # session_id
session_delete_requested = Signal(str)  # session_id
new_session_requested = Signal()

# 兼容性信号（保留向后兼容）
new_chat_requested = Signal()  # 等同于new_session_requested
manage_chats_requested = Signal()  # 暂时保留
```

### 2. 同步触发兼容信号

添加`_on_new_session_requested`方法，在新建会话时同时触发新旧两个信号：

```python
def _connect_signals(self):
    """连接信号"""
    # ...
    self.session_list_panel.new_session_requested.connect(self._on_new_session_requested)

def _on_new_session_requested(self):
    """处理新建会话请求，发射兼容信号"""
    self.new_session_requested.emit()
    self.new_chat_requested.emit()  # 向后兼容
```

## 修复验证

运行测试脚本验证修复：

```bash
python tests/test_sidebar_fix.py
```

**测试结果**:
```
✓ 所有信号都存在！
✓ 兼容性信号工作正常！
✓ CherryMainWindow 导入成功

总计: 2/2 测试通过
🎉 所有测试通过！修复成功！
```

## 修改文件

- `components/chat/widgets/sidebar.py`
  - 第33-35行：重新添加兼容性信号定义
  - 第122行：修改信号连接方式
  - 第124-127行：新增`_on_new_session_requested`方法

## 向后兼容性

- ✅ `new_chat_requested`信号保留，向后兼容
- ✅ `manage_chats_requested`信号保留，向后兼容
- ✅ 新增`new_session_requested`信号，推荐使用
- ✅ 主窗口无需修改，直接可用

## 未来优化建议

可以逐步将`main_window.py`中的信号连接改为使用新的`new_session_requested`信号：

```python
# 推荐的新写法
self.sidebar.new_session_requested.connect(self._on_new_tab)

# 而不是旧的
self.sidebar.new_chat_requested.connect(self._on_new_tab)
```

但目前两种方式都可以正常工作。
