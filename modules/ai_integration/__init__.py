# -*- coding: utf-8 -*-
"""
AI Integration Module
统一的AI服务集成层,支持多种AI模型提供商
"""

from .base import AIServiceBase, AIServiceConfig
from .exceptions import (
    AIServiceError,
    APIKeyError,
    NetworkError,
    ModelNotAvailableError,
    RateLimitError,
    InvalidRequestError,
    ServiceUnavailableError,
    ContentFilterError,
)
from .registry import AIServiceRegistry
from .config_loader import AIConfigLoader
from .providers.openai_service import OpenAIService

# 导入新版API Providers（用于ChatController）
from .api_providers.openai_provider import OpenAIProvider as NewOpenAIProvider
from .api_providers.base_provider import ProviderConfig as NewProviderConfig, ChatMessage as ProviderChatMessage
from .streaming_handler import StreamingHandler as NewStreamingHandler

# 自动注册OpenAI服务（旧版异步实现）
AIServiceRegistry.register('openai', OpenAIService)

# ===== 向后兼容性别名 =====
# ChatController使用新版同步Provider（OpenAIProvider from api_providers）
OpenAIProvider = NewOpenAIProvider  # 指向新版同步实现
ProviderConfig = NewProviderConfig  # 新版配置类
StreamingHandler = NewStreamingHandler  # 新版流式处理器（使用QThread）
ChatMessage = ProviderChatMessage  # 新版消息类

# 保留旧版别名供其他代码使用
AIServiceConfig = AIServiceConfig  # 旧版异步配置

# 临时占位类 - 等待实现完整功能
class ChatManager:
    """对话管理器占位类"""
    def __init__(self):
        self.messages = []

    def add_message(self, role, content):
        """添加消息到历史"""
        from .api_providers.base_provider import ChatMessage as Msg
        msg = Msg(role=role, content=content)
        self.messages.append(msg)

    def get_context_messages(self):
        """获取上下文消息"""
        return self.messages

    def save_state(self):
        """保存状态（占位）"""
        pass


__all__ = [
    # Base classes
    'AIServiceBase',
    'AIServiceConfig',

    # Exceptions
    'AIServiceError',
    'APIKeyError',
    'NetworkError',
    'ModelNotAvailableError',
    'RateLimitError',
    'InvalidRequestError',
    'ServiceUnavailableError',
    'ContentFilterError',

    # Registry
    'AIServiceRegistry',

    # Config
    'AIConfigLoader',

    # Services
    'OpenAIService',

    # 向后兼容别名（新版同步API）
    'OpenAIProvider',
    'ProviderConfig',
    'StreamingHandler',
    'ChatMessage',
    'ChatManager',
]
