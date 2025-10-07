# -*- coding: utf-8 -*-
"""
OpenAI Service Integration Tests
测试OpenAI服务实现（包括流式输出、错误处理、配置加载等）
"""

import sys
from pathlib import Path
import pytest
import httpx
import respx
import json
from typing import AsyncIterator

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.ai_integration.providers.openai_service import OpenAIService
from modules.ai_integration.config_loader import AIConfigLoader
from modules.ai_integration.exceptions import (
    APIKeyError,
    NetworkError,
    RateLimitError,
    ModelNotAvailableError,
    InvalidRequestError,
    ServiceUnavailableError,
)


class TestOpenAIServiceBasics:
    """测试OpenAI服务基础功能"""

    def test_service_creation_with_default_config(self):
        """测试使用默认配置创建服务"""
        service = OpenAIService({})

        assert service.config.api_key == OpenAIService.DEFAULT_API_KEY
        assert service.config.base_url == OpenAIService.DEFAULT_BASE_URL
        assert service.config.model == OpenAIService.DEFAULT_MODEL

    def test_service_creation_with_custom_config(self):
        """测试使用自定义配置创建服务"""
        config = {
            'api_key': 'custom-key-123',
            'base_url': 'https://custom.api.com/v1',
            'model': 'gpt-4',
            'timeout': 60
        }

        service = OpenAIService(config)

        assert service.config.api_key == 'custom-key-123'
        assert service.config.base_url == 'https://custom.api.com/v1'
        assert service.config.model == 'gpt-4'
        assert service.config.timeout == 60

    def test_get_available_models(self):
        """测试获取可用模型列表"""
        service = OpenAIService({})

        models = service.get_available_models()

        # 应包含GPT系列
        assert 'gpt-4' in models
        assert 'gpt-3.5-turbo' in models

        # 应包含Gemini系列
        assert 'gemini-2.5-pro' in models
        assert 'gemini-1.5-pro' in models

        # 应包含Claude系列
        assert 'claude-3-opus' in models

    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = {
            'api_key': 'test-key-123',
            'base_url': 'https://api.test.com/v1',
            'model': 'gemini-2.5-pro',
            'timeout': 30
        }

        service = OpenAIService(config)
        assert service.validate_config() is True

    def test_validate_config_empty_api_key(self):
        """测试空API密钥验证失败"""
        config = {
            'api_key': '',
            'model': 'gpt-4'
        }

        service = OpenAIService(config)
        # 会使用默认key，所以应该valid
        assert service.validate_config() is True

    def test_validate_config_invalid_model(self):
        """测试无效模型验证失败"""
        config = {
            'api_key': 'test-key',
            'model': 'invalid-model-xyz'
        }

        service = OpenAIService(config)
        assert service.validate_config() is False

    def test_validate_config_invalid_url(self):
        """测试无效URL验证失败"""
        config = {
            'api_key': 'test-key',
            'base_url': 'not-a-valid-url',
            'model': 'gpt-4'
        }

        service = OpenAIService(config)
        assert service.validate_config() is False

    def test_estimate_tokens_english(self):
        """测试英文文本token估算"""
        service = OpenAIService({})

        text = "Hello, World! This is a test."
        tokens = service.estimate_tokens(text)

        # 英文约4字符/token
        expected = len(text) / 4
        assert abs(tokens - expected) <= 2  # 允许±2误差

    def test_estimate_tokens_chinese(self):
        """测试中文文本token估算"""
        service = OpenAIService({})

        text = "你好世界！这是一个测试。"
        tokens = service.estimate_tokens(text)

        # 中文约1.5字符/token
        expected = len(text) / 1.5
        assert abs(tokens - expected) <= 2

    def test_estimate_tokens_mixed(self):
        """测试中英文混合token估算"""
        service = OpenAIService({})

        text = "Hello世界! This is一个test测试。"
        tokens = service.estimate_tokens(text)

        # 应该大于0
        assert tokens > 0

    def test_estimate_tokens_empty(self):
        """测试空文本token估算"""
        service = OpenAIService({})

        tokens = service.estimate_tokens("")
        assert tokens == 0

    def test_get_service_name(self):
        """测试获取服务名称"""
        service = OpenAIService({})

        name = service.get_service_name()
        assert name == 'openai'


class TestOpenAIServiceStreaming:
    """测试OpenAI服务流式输出"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_streaming_success(self):
        """测试成功的流式消息发送"""
        # Mock流式响应
        mock_route = respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                text="""data: {"choices":[{"delta":{"content":"Hello"}}]}
data: {"choices":[{"delta":{"content":" "}}]}
data: {"choices":[{"delta":{"content":"World"}}]}
data: {"choices":[{"delta":{"content":"!"}}]}
data: [DONE]
"""
            )
        )

        service = OpenAIService({})

        # 发送消息
        chunks = []
        async for chunk in service.send_message(
            prompt="Test prompt",
            context=[],
            streaming=True
        ):
            chunks.append(chunk)

        # 验证结果
        assert ''.join(chunks) == "Hello World!"
        assert mock_route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_with_context(self):
        """测试带上下文的消息发送"""
        mock_route = respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                text='data: {"choices":[{"delta":{"content":"Response"}}]}\ndata: [DONE]\n'
            )
        )

        service = OpenAIService({})

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]

        chunks = []
        async for chunk in service.send_message(
            prompt="New message",
            context=context,
            streaming=True
        ):
            chunks.append(chunk)

        assert mock_route.called

        # 验证请求payload包含完整对话历史
        request = mock_route.calls.last.request
        payload = json.loads(request.content)

        assert len(payload['messages']) == 3
        assert payload['messages'][0]['content'] == "Previous message"
        assert payload['messages'][1]['content'] == "Previous response"
        assert payload['messages'][2]['content'] == "New message"

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_with_params(self):
        """测试带自定义参数的消息发送"""
        mock_route = respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                text='data: {"choices":[{"delta":{"content":"OK"}}]}\ndata: [DONE]\n'
            )
        )

        service = OpenAIService({})

        async for chunk in service.send_message(
            prompt="Test",
            context=[],
            temperature=0.9,
            max_tokens=1000,
            top_p=0.95
        ):
            pass

        # 验证请求参数
        request = mock_route.calls.last.request
        payload = json.loads(request.content)

        assert payload['temperature'] == 0.9
        assert payload['max_tokens'] == 1000
        assert payload['top_p'] == 0.95


class TestOpenAIServiceErrors:
    """测试OpenAI服务错误处理"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_key_error_401(self):
        """测试401 API密钥错误"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"message": "Invalid API key"}}
            )
        )

        service = OpenAIService({})

        with pytest.raises(APIKeyError, match="Invalid API key"):
            async for chunk in service.send_message("Test", []):
                pass

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limit_error_429(self):
        """测试429速率限制错误"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                429,
                json={"error": {"message": "Rate limit exceeded"}},
                headers={"Retry-After": "60"}
            )
        )

        service = OpenAIService({})

        with pytest.raises(RateLimitError) as exc_info:
            async for chunk in service.send_message("Test", []):
                pass

        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    @respx.mock
    async def test_model_not_found_404(self):
        """测试404模型不存在错误"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"message": "Model not found"}}
            )
        )

        service = OpenAIService({})

        with pytest.raises(ModelNotAvailableError, match="Model not found"):
            async for chunk in service.send_message("Test", []):
                pass

    @pytest.mark.asyncio
    @respx.mock
    async def test_invalid_request_400(self):
        """测试400无效请求错误"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                400,
                json={"error": {"message": "Invalid request parameters"}}
            )
        )

        service = OpenAIService({})

        with pytest.raises(InvalidRequestError, match="Invalid request"):
            async for chunk in service.send_message("Test", []):
                pass

    @pytest.mark.asyncio
    @respx.mock
    async def test_service_unavailable_503(self):
        """测试503服务不可用错误"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            return_value=httpx.Response(
                503,
                json={"error": {"message": "Service temporarily unavailable"}}
            )
        )

        service = OpenAIService({})

        with pytest.raises(ServiceUnavailableError, match="Service unavailable"):
            async for chunk in service.send_message("Test", []):
                pass

    @pytest.mark.asyncio
    @respx.mock
    async def test_network_timeout(self):
        """测试网络超时"""
        respx.post("https://api.kkyyxx.xyz/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        service = OpenAIService({'timeout': 1})

        with pytest.raises(NetworkError, match="timeout"):
            async for chunk in service.send_message("Test", []):
                pass


class TestAIConfigLoader:
    """测试AI配置加载器"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        config = AIConfigLoader.get_default_config()

        assert 'active_service' in config
        assert 'services' in config

        # 验证默认使用Gemini配置
        assert config['active_service'] == 'openai'
        openai_config = config['services']['openai']

        assert openai_config['api_key'] == 'UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t'
        assert openai_config['base_url'] == 'https://api.kkyyxx.xyz/v1'
        assert openai_config['model'] == 'gemini-2.5-pro'

    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = AIConfigLoader.get_default_config()
        loader = AIConfigLoader()

        assert loader.validate_config(config) is True

    def test_validate_config_missing_active_service(self):
        """测试缺少active_service验证失败"""
        config = {
            "services": {
                "openai": {"api_key": "test", "model": "gpt-4"}
            }
        }
        loader = AIConfigLoader()

        assert loader.validate_config(config) is False

    def test_validate_config_missing_services(self):
        """测试缺少services验证失败"""
        config = {
            "active_service": "openai"
        }
        loader = AIConfigLoader()

        assert loader.validate_config(config) is False

    def test_validate_config_active_service_not_exist(self):
        """测试active_service不存在验证失败"""
        config = {
            "active_service": "nonexistent",
            "services": {
                "openai": {"api_key": "test", "model": "gpt-4"}
            }
        }
        loader = AIConfigLoader()

        assert loader.validate_config(config) is False

    def test_validate_config_missing_required_field(self):
        """测试缺少必需字段验证失败"""
        config = {
            "active_service": "openai",
            "services": {
                "openai": {"api_key": "test"}  # 缺少model
            }
        }
        loader = AIConfigLoader()

        assert loader.validate_config(config) is False


if __name__ == '__main__':
    print("Running OpenAI Service Integration Tests...")
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
