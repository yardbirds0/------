# -*- coding: utf-8 -*-
"""
AI Service Registry
AI服务注册表,管理所有可用的AI服务提供商
"""

from typing import Type, Dict, List, Optional
from .base import AIServiceBase
from .exceptions import AIServiceError


class AIServiceRegistry:
    """
    AI服务注册表
    
    使用注册表模式管理所有AI服务提供商,支持动态注册和查找
    """
    
    # 类变量: 存储所有已注册的服务
    _services: Dict[str, Type[AIServiceBase]] = {}
    
    @classmethod
    def register(cls, name: str, service_class: Type[AIServiceBase]):
        """
        注册新的AI服务提供商
        
        Args:
            name: 服务名称(如 'openai', 'claude', 'gemini')
            service_class: AI服务类(必须继承自AIServiceBase)
            
        Raises:
            TypeError: 如果service_class不是AIServiceBase的子类
            ValueError: 如果服务名称已存在
        """
        if not issubclass(service_class, AIServiceBase):
            raise TypeError(
                f"{service_class.__name__} must inherit from AIServiceBase"
            )
        
        if name in cls._services:
            raise ValueError(
                f"Service '{name}' is already registered"
            )

        cls._services[name] = service_class
        # Registered successfully (removed unicode character for compatibility)
    
    @classmethod
    def unregister(cls, name: str):
        """
        注销AI服务提供商
        
        Args:
            name: 服务名称
            
        Raises:
            ValueError: 如果服务不存在
        """
        if name not in cls._services:
            raise ValueError(f"Service '{name}' is not registered")
        
        del cls._services[name]
        print(f"✓ Unregistered AI service: {name}")
    
    @classmethod
    def get_service(cls, name: str, config: dict) -> AIServiceBase:
        """
        根据名称获取AI服务实例
        
        Args:
            name: 服务名称
            config: 服务配置字典
            
        Returns:
            AIServiceBase: 服务实例
            
        Raises:
            ValueError: 如果服务未注册
            AIServiceError: 如果服务初始化失败
        """
        if name not in cls._services:
            available = ', '.join(cls.list_services())
            raise ValueError(
                f"Unknown service: '{name}'. "
                f"Available services: {available}"
            )
        
        service_class = cls._services[name]
        
        try:
            return service_class(config)
        except Exception as e:
            raise AIServiceError(
                f"Failed to initialize service '{name}': {str(e)}"
            ) from e
    
    @classmethod
    def list_services(cls) -> List[str]:
        """
        列出所有已注册的服务名称
        
        Returns:
            服务名称列表
        """
        return list(cls._services.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            name: 服务名称
            
        Returns:
            True if registered, False otherwise
        """
        return name in cls._services
    
    @classmethod
    def get_service_class(cls, name: str) -> Optional[Type[AIServiceBase]]:
        """
        获取服务类(不实例化)
        
        Args:
            name: 服务名称
            
        Returns:
            服务类,如果不存在则返回None
        """
        return cls._services.get(name)
    
    @classmethod
    def clear(cls):
        """
        清空所有已注册的服务(主要用于测试)
        """
        cls._services.clear()
