# -*- coding: utf-8 -*-
"""
AI Service Base Tests
测试AI服务抽象基类、异常层次和服务注册表
"""

import sys
from pathlib import Path
import pytest
from typing import AsyncIterator, List, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.ai_integration.base import AIServiceBase, AIServiceConfig
from modules.ai_integration.exceptions import (
    AIServiceError,
    APIKeyError,
    NetworkError,
    ModelNotAvailableError,
    RateLimitError,
)
from modules.ai_integration.registry import AIServiceRegistry


class MockAIService(AIServiceBase):
    """测试用的模拟AI服务"""
    
    async def send_message(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        streaming: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        """模拟流式输出"""
        for char in "Hello, World!":
            yield char
    
    def get_available_models(self) -> List[str]:
        return ['mock-model-1', 'mock-model-2']
    
    def validate_config(self) -> bool:
        return bool(self.config.api_key)
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class TestAIServiceConfig:
    """测试AIServiceConfig配置模型"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = AIServiceConfig(
            api_key='test-key',
            model='gpt-4',
            timeout=30
        )
        
        assert config.api_key == 'test-key'
        assert config.model == 'gpt-4'
        assert config.timeout == 30
        assert config.base_url is None
    
    def test_config_with_base_url(self):
        """测试包含base_url的配置"""
        config = AIServiceConfig(
            api_key='test-key',
            base_url='https://api.example.com',
            model='gpt-4'
        )
        
        assert config.base_url == 'https://api.example.com'
    
    def test_config_validation_fails_without_api_key(self):
        """测试缺少API密钥时配置验证失败"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AIServiceConfig(model='gpt-4')
    
    def test_config_timeout_validation(self):
        """测试超时时间验证"""
        # 超时时间必须在1-300秒之间
        with pytest.raises(Exception):
            AIServiceConfig(
                api_key='test-key',
                model='gpt-4',
                timeout=0  # 无效
            )


class TestAIServiceBase:
    """测试AIServiceBase抽象基类"""
    
    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            AIServiceBase({'api_key': 'test', 'model': 'test'})
    
    def test_mock_service_creation(self):
        """测试创建模拟服务"""
        config = {
            'api_key': 'test-key-123',
            'model': 'mock-model-1',
            'timeout': 30
        }
        
        service = MockAIService(config)
        
        assert service.config.api_key == 'test-key-123'
        assert service.config.model == 'mock-model-1'
        assert service.validate_config() is True
    
    def test_get_available_models(self):
        """测试获取可用模型列表"""
        service = MockAIService({
            'api_key': 'test',
            'model': 'test'
        })
        
        models = service.get_available_models()
        assert 'mock-model-1' in models
        assert 'mock-model-2' in models
    
    def test_estimate_tokens(self):
        """测试token估算"""
        service = MockAIService({
            'api_key': 'test',
            'model': 'test'
        })
        
        text = "Hello, World!"
        tokens = service.estimate_tokens(text)
        assert tokens > 0
    
    def test_get_service_name(self):
        """测试获取服务名称"""
        service = MockAIService({
            'api_key': 'test',
            'model': 'test'
        })
        
        name = service.get_service_name()
        assert name == 'mockai'  # MockAIService -> mockai


class TestExceptionHierarchy:
    """测试异常层次结构"""
    
    def test_base_exception(self):
        """测试基础异常"""
        exc = AIServiceError("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)
    
    def test_api_key_error(self):
        """测试API密钥错误"""
        exc = APIKeyError("Invalid API key")
        assert isinstance(exc, AIServiceError)
    
    def test_network_error(self):
        """测试网络错误"""
        exc = NetworkError("Connection timeout")
        assert isinstance(exc, AIServiceError)
    
    def test_rate_limit_error_with_retry_after(self):
        """测试带重试时间的速率限制错误"""
        exc = RateLimitError("Rate limit exceeded", retry_after=60)
        assert exc.retry_after == 60
        assert isinstance(exc, AIServiceError)


class TestAIServiceRegistry:
    """测试AI服务注册表"""
    
    def setup_method(self):
        """每个测试前清空注册表"""
        AIServiceRegistry.clear()
    
    def test_register_service(self):
        """测试注册服务"""
        AIServiceRegistry.register('mock', MockAIService)
        
        assert AIServiceRegistry.is_registered('mock')
        assert 'mock' in AIServiceRegistry.list_services()
    
    def test_register_duplicate_service_raises_error(self):
        """测试重复注册相同服务抛出错误"""
        AIServiceRegistry.register('mock', MockAIService)
        
        with pytest.raises(ValueError, match="already registered"):
            AIServiceRegistry.register('mock', MockAIService)
    
    def test_register_invalid_service_class_raises_error(self):
        """测试注册非AIServiceBase子类抛出错误"""
        class InvalidService:
            pass
        
        with pytest.raises(TypeError, match="must inherit from AIServiceBase"):
            AIServiceRegistry.register('invalid', InvalidService)
    
    def test_get_service(self):
        """测试获取服务实例"""
        AIServiceRegistry.register('mock', MockAIService)
        
        config = {
            'api_key': 'test-key',
            'model': 'test-model'
        }
        
        service = AIServiceRegistry.get_service('mock', config)
        
        assert isinstance(service, MockAIService)
        assert service.config.api_key == 'test-key'
    
    def test_get_unregistered_service_raises_error(self):
        """测试获取未注册的服务抛出错误"""
        with pytest.raises(ValueError, match="Unknown service"):
            AIServiceRegistry.get_service('nonexistent', {})
    
    def test_list_services(self):
        """测试列出所有服务"""
        AIServiceRegistry.register('mock1', MockAIService)
        AIServiceRegistry.register('mock2', MockAIService)
        
        services = AIServiceRegistry.list_services()
        
        assert len(services) == 2
        assert 'mock1' in services
        assert 'mock2' in services
    
    def test_unregister_service(self):
        """测试注销服务"""
        AIServiceRegistry.register('mock', MockAIService)
        assert AIServiceRegistry.is_registered('mock')
        
        AIServiceRegistry.unregister('mock')
        assert not AIServiceRegistry.is_registered('mock')
    
    def test_get_service_class(self):
        """测试获取服务类(不实例化)"""
        AIServiceRegistry.register('mock', MockAIService)
        
        service_class = AIServiceRegistry.get_service_class('mock')
        
        assert service_class == MockAIService
        assert issubclass(service_class, AIServiceBase)


if __name__ == '__main__':
    print("Running AI Service Base Tests...")
    pytest.main([__file__, '-v'])
