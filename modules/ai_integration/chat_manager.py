# -*- coding: utf-8 -*-
"""
Chat Manager
管理对话历史、上下文窗口和持久化存储
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from .api_providers.base_provider import ChatMessage

logger = logging.getLogger(__name__)


class ChatManager:
    """
    对话管理器
    负责对话历史的存储、检索和上下文窗口管理
    """

    MAX_HISTORY_LENGTH = 50  # 最大历史消息数
    DEFAULT_CONTEXT_WINDOW = 10  # 默认上下文窗口大小（消息对数）
    CACHE_DIR = Path(".cache")

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化对话管理器

        Args:
            session_id: 会话 ID，用于区分不同对话
        """
        self.session_id = session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.messages: List[ChatMessage] = []
        self.context_window_size = self.DEFAULT_CONTEXT_WINDOW
        self.total_tokens = 0

        # 确保缓存目录存在
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.state_file = self.CACHE_DIR / "chat_state.json"

    def add_message(self, role: str, content: str) -> ChatMessage:
        """
        添加消息到历史

        Args:
            role: 消息角色 ('user', 'assistant', 'system')
            content: 消息内容

        Returns:
            创建的 ChatMessage 对象
        """
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)

        # 限制历史长度
        if len(self.messages) > self.MAX_HISTORY_LENGTH:
            self.messages = self.messages[-self.MAX_HISTORY_LENGTH:]

        logger.debug(f"添加消息: {role}, 长度: {len(content)}, 总消息数: {len(self.messages)}")
        return message

    def get_context_messages(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        获取上下文消息（用于发送给 API）

        Args:
            max_messages: 最大消息数量（默认使用 context_window_size）
            max_tokens: 最大 token 数量（可选，用于更精确的控制）

        Returns:
            上下文消息列表
        """
        if not self.messages:
            return []

        # 确定消息数量限制
        limit = max_messages or (self.context_window_size * 2)  # 用户+助手=1对=2条消息

        # 取最近的 N 条消息
        context = self.messages[-limit:]

        # TODO: 如果需要，可以基于 max_tokens 进一步裁剪
        # 这需要准确的 token 计数（tiktoken 库）

        return context

    def clear_history(self):
        """清空对话历史"""
        self.messages.clear()
        self.total_tokens = 0
        logger.info("对话历史已清空")

    def get_last_message(self) -> Optional[ChatMessage]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None

    def get_message_count(self) -> int:
        """获取消息总数"""
        return len(self.messages)

    def save_state(self) -> bool:
        """
        保存对话状态到文件

        Returns:
            是否保存成功
        """
        try:
            state = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                    }
                    for msg in self.messages
                ],
                'total_tokens': self.total_tokens,
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            logger.info(f"对话状态已保存: {self.state_file}")
            return True

        except Exception as e:
            logger.error(f"保存对话状态失败: {e}")
            return False

    def load_state(self) -> bool:
        """
        从文件加载对话状态

        Returns:
            是否加载成功
        """
        try:
            if not self.state_file.exists():
                logger.info("未找到对话状态文件")
                return False

            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 恢复消息历史
            self.messages = [
                ChatMessage(role=msg['role'], content=msg['content'])
                for msg in state.get('messages', [])
            ]

            self.total_tokens = state.get('total_tokens', 0)
            loaded_session = state.get('session_id', 'unknown')

            logger.info(f"对话状态已加载: {loaded_session}, 消息数: {len(self.messages)}")
            return True

        except Exception as e:
            logger.error(f"加载对话状态失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取对话统计信息

        Returns:
            统计数据字典
        """
        user_messages = sum(1 for msg in self.messages if msg.role == 'user')
        assistant_messages = sum(1 for msg in self.messages if msg.role == 'assistant')

        return {
            'session_id': self.session_id,
            'total_messages': len(self.messages),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'total_tokens': self.total_tokens,
            'context_window_size': self.context_window_size,
        }

    def set_context_window_size(self, size: int):
        """
        设置上下文窗口大小

        Args:
            size: 窗口大小（消息对数）
        """
        if size < 1:
            raise ValueError("上下文窗口大小必须 >= 1")
        self.context_window_size = size
        logger.info(f"上下文窗口大小已设置为: {size}")

    def update_token_count(self, token_count: int):
        """
        更新总 token 计数

        Args:
            token_count: 本次对话消耗的 token 数
        """
        self.total_tokens += token_count
        logger.debug(f"Token 计数更新: +{token_count}, 总计: {self.total_tokens}")
