# -*- coding: utf-8 -*-
"""
AI Service Base Classes
定义所有AI服务提供商必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class AIServiceConfig(BaseModel):
    """
    通用AI服务配置

    所有AI服务提供商的配置都应继承此类
    """
    model_config = ConfigDict(extra='allow')  # 允许额外字段以支持特定提供商的配置

    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL(可选)")
    model: str = Field(..., description="使用的模型名称")
    timeout: int = Field(30, description="请求超时时间(秒)", ge=1, le=300)


class AIServiceBase(ABC):
    """
    AI服务抽象基类
    
    所有AI服务提供商(OpenAI, Claude, Gemini等)必须继承并实现此类
    """
    
    def __init__(self, config: dict):
        """
        初始化AI服务
        
        Args:
            config: 服务配置字典
        """
        self.config = self._validate_config(config)
    
    def _validate_config(self, config: dict) -> AIServiceConfig:
        """
        验证并解析配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证后的配置对象
            
        Raises:
            ValidationError: 配置验证失败
        """
        return AIServiceConfig(**config)
    
    @abstractmethod
    async def send_message(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        streaming: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        发送消息并获取流式响应
        
        Args:
            prompt: 用户输入的消息
            context: 对话上下文历史 [{"role": "user/assistant", "content": "..."}]
            streaming: 是否启用流式输出
            **kwargs: 额外参数(如temperature, max_tokens等)
            
        Yields:
            str: 流式返回的文本片段
            
        Raises:
            APIKeyError: API密钥无效
            NetworkError: 网络错误
            ModelNotAvailableError: 模型不可用
            RateLimitError: 超出速率限制
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            模型名称列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 要估算的文本
            
        Returns:
            估算的token数量
        """
        pass
    
    def get_service_name(self) -> str:
        """
        获取服务名称
        
        Returns:
            服务提供商名称
        """
        return self.__class__.__name__.replace('Service', '').lower()
