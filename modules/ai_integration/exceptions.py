# -*- coding: utf-8 -*-
"""
AI Service Exceptions
AI服务异常层次结构
"""


class AIServiceError(Exception):
    """
    AI服务基础异常类
    
    所有AI服务相关的异常都应继承此类
    """
    pass


class APIKeyError(AIServiceError):
    """
    API密钥错误
    
    当API密钥缺失、无效或权限不足时抛出
    """
    pass


class NetworkError(AIServiceError):
    """
    网络错误
    
    当网络连接失败、超时或其他网络问题时抛出
    """
    pass


class ModelNotAvailableError(AIServiceError):
    """
    模型不可用错误
    
    当请求的模型不存在或暂时不可用时抛出
    """
    pass


class RateLimitError(AIServiceError):
    """
    速率限制错误
    
    当超出API调用速率限制时抛出
    """
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        """
        Args:
            message: 错误信息
            retry_after: 建议重试等待时间(秒)
        """
        super().__init__(message)
        self.retry_after = retry_after


class InvalidRequestError(AIServiceError):
    """
    无效请求错误
    
    当请求参数无效或格式不正确时抛出
    """
    pass


class ServiceUnavailableError(AIServiceError):
    """
    服务不可用错误
    
    当AI服务暂时不可用(如维护、过载)时抛出
    """
    pass


class ContentFilterError(AIServiceError):
    """
    内容过滤错误
    
    当内容违反内容政策被过滤时抛出
    """
    pass
