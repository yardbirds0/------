# -*- coding: utf-8 -*-
"""
Base Provider Interface
定义所有 LLM 服务提供商必须实现的基础接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterator, List
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """提供商类型枚举"""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class ProviderConfig:
    """提供商配置数据类"""
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4-turbo"
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 30
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'api_key': self.api_key,
            'base_url': self.base_url,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
        }


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # 'system', 'user', 'assistant'
    content: str

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {'role': self.role, 'content': self.content}


@dataclass
class ChatResponse:
    """AI 响应数据类"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None  # {'prompt_tokens': x, 'completion_tokens': y, 'total_tokens': z}
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """
    LLM 服务提供商基类
    定义所有提供商必须实现的核心方法
    """

    def __init__(self, config: ProviderConfig):
        """
        初始化提供商

        Args:
            config: 提供商配置对象
        """
        self.config = config
        self.provider_type: ProviderType = ProviderType.CUSTOM

    @abstractmethod
    def validate_connection(self) -> tuple[bool, str]:
        """
        验证 API 连接是否有效

        Returns:
            (是否成功, 错误信息或成功消息)
        """
        pass

    @abstractmethod
    def send_message(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """
        发送聊天消息（非流式）

        Args:
            messages: 消息历史列表
            stream: 是否使用流式响应
            system_prompt: 可选的系统提示词

        Returns:
            ChatResponse 对象

        Raises:
            ProviderError: API 调用失败时抛出
        """
        pass

    @abstractmethod
    def stream_message(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        """
        发送聊天消息（流式响应）

        Args:
            messages: 消息历史列表
            system_prompt: 可选的系统提示词

        Yields:
            str: 响应文本片段

        Raises:
            ProviderError: API 调用失败时抛出
        """
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 Token 数量

        Args:
            text: 要估算的文本

        Returns:
            估算的 token 数量
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型的信息

        Returns:
            包含模型名称、参数限制等信息的字典
        """
        return {
            'model': self.config.model,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'provider_type': self.provider_type.value,
        }


class ProviderError(Exception):
    """提供商相关错误的基类"""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class RateLimitError(ProviderError):
    """速率限制错误"""
    pass


class AuthenticationError(ProviderError):
    """认证失败错误"""
    pass


class NetworkError(ProviderError):
    """网络连接错误"""
    pass


class InvalidRequestError(ProviderError):
    """无效请求错误"""
    pass
