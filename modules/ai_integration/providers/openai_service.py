# -*- coding: utf-8 -*-
"""
OpenAI Service Implementation
支持OpenAI API及其兼容接口（如Gemini转发、Claude转发等）
"""

import httpx
import json
import re
from typing import AsyncIterator, List, Dict, Optional
from ..base import AIServiceBase, AIServiceConfig
from ..exceptions import (
    APIKeyError,
    NetworkError,
    ModelNotAvailableError,
    RateLimitError,
    InvalidRequestError,
    ServiceUnavailableError,
)


class OpenAIService(AIServiceBase):
    """
    OpenAI GPT及兼容API服务

    支持：
    - OpenAI官方API（GPT系列）
    - OpenAI兼容转发服务（Gemini、Claude等）
    - 自定义base_url
    - 流式输出
    - 完善的错误处理
    """

    # 支持的模型列表（包含GPT和Gemini系列）
    SUPPORTED_MODELS = [
        # OpenAI GPT系列
        'gpt-4',
        'gpt-4-turbo',
        'gpt-4-turbo-preview',
        'gpt-4-0125-preview',
        'gpt-4-1106-preview',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo-0125',
        # Google Gemini系列（通过转发）
        'gemini-2.5-pro',
        'gemini-2.0-flash-exp',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        # Anthropic Claude系列（通过转发）
        'claude-3-opus',
        'claude-3-sonnet',
        'claude-3-haiku',
    ]

    # 默认配置（使用用户提供的Gemini转发服务）
    DEFAULT_BASE_URL = 'https://api.kkyyxx.xyz/v1'
    DEFAULT_API_KEY = 'UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t'
    DEFAULT_MODEL = 'gemini-2.5-pro'

    def __init__(self, config: dict):
        """
        初始化OpenAI服务

        Args:
            config: 配置字典，支持以下字段：
                - api_key: API密钥（默认使用内置Gemini转发密钥）
                - base_url: API基础URL（默认使用Gemini转发服务）
                - model: 模型名称（默认gemini-2.5-pro）
                - timeout: 超时时间（秒，默认30）
        """
        # 使用默认配置补全缺失的字段（在Pydantic验证之前）
        if 'api_key' not in config or not config.get('api_key'):
            config['api_key'] = self.DEFAULT_API_KEY

        if 'base_url' not in config or not config.get('base_url'):
            config['base_url'] = self.DEFAULT_BASE_URL

        if 'model' not in config or not config.get('model'):
            config['model'] = self.DEFAULT_MODEL

        # 调用父类初始化（会进行Pydantic验证）
        super().__init__(config)

        # 创建异步HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            },
            timeout=self.config.timeout
        )

    async def send_message(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        streaming: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        发送消息到OpenAI API并获取流式响应

        Args:
            prompt: 用户输入的消息
            context: 对话上下文历史 [{"role": "user/assistant", "content": "..."}]
            streaming: 是否启用流式输出（默认True）
            **kwargs: 额外参数
                - temperature: 温度参数（0-2，默认0.7）
                - max_tokens: 最大token数（默认4096）
                - top_p: nucleus sampling参数（默认1.0）
                - frequency_penalty: 频率惩罚（默认0）
                - presence_penalty: 存在惩罚（默认0）

        Yields:
            str: 流式返回的文本片段

        Raises:
            APIKeyError: API密钥无效
            NetworkError: 网络错误或超时
            ModelNotAvailableError: 模型不可用
            RateLimitError: 超出速率限制
            InvalidRequestError: 请求参数无效
            ServiceUnavailableError: 服务不可用
        """
        # 构建消息列表
        messages = context + [{"role": "user", "content": prompt}]

        # 构建请求payload
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": streaming,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 4096),
            "top_p": kwargs.get('top_p', 1.0),
            "frequency_penalty": kwargs.get('frequency_penalty', 0),
            "presence_penalty": kwargs.get('presence_penalty', 0),
        }

        try:
            # 发送流式请求
            async with self.client.stream(
                'POST',
                '/chat/completions',
                json=payload
            ) as response:
                # 先检查HTTP状态码（在读取流之前）
                if response.status_code != 200:
                    # 读取完整响应内容用于错误处理
                    await response.aread()
                    await self._handle_http_errors(response)

                # 处理流式响应
                async for line in response.aiter_lines():
                    # SSE格式: "data: {...}"
                    if line.startswith('data: '):
                        data_str = line[6:].strip()

                        # 流结束标记
                        if data_str == '[DONE]':
                            break

                        try:
                            # 解析JSON数据
                            data = json.loads(data_str)

                            # 提取内容增量
                            if data.get('choices'):
                                choice = data['choices'][0]
                                delta = choice.get('delta', {})
                                content = delta.get('content', '')

                                if content:
                                    yield content

                        except json.JSONDecodeError:
                            # 忽略无效的JSON行
                            continue

        except httpx.TimeoutException:
            raise NetworkError(
                f"Request timeout after {self.config.timeout} seconds"
            )
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            if not isinstance(e, (APIKeyError, NetworkError, ModelNotAvailableError,
                                RateLimitError, InvalidRequestError, ServiceUnavailableError)):
                raise NetworkError(f"Unexpected error: {str(e)}")
            raise

    async def _handle_http_errors(self, response: httpx.Response):
        """
        处理HTTP错误状态码

        Args:
            response: HTTP响应对象

        Raises:
            APIKeyError: 401 Unauthorized
            RateLimitError: 429 Too Many Requests
            ModelNotAvailableError: 404 Not Found
            InvalidRequestError: 400 Bad Request
            ServiceUnavailableError: 503 Service Unavailable
            NetworkError: 其他错误
        """
        if response.status_code == 200:
            return

        # 尝试解析错误消息
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
        except:
            error_message = response.text or f"HTTP {response.status_code}"

        # 根据状态码抛出相应异常
        if response.status_code == 401:
            raise APIKeyError(f"Invalid API key: {error_message}")
        elif response.status_code == 429:
            # 尝试获取重试时间
            retry_after = response.headers.get('Retry-After')
            retry_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                retry_after=retry_seconds
            )
        elif response.status_code == 404:
            raise ModelNotAvailableError(
                f"Model not found: {error_message}"
            )
        elif response.status_code == 400:
            raise InvalidRequestError(
                f"Invalid request: {error_message}"
            )
        elif response.status_code == 503:
            raise ServiceUnavailableError(
                f"Service unavailable: {error_message}"
            )
        else:
            raise NetworkError(
                f"HTTP {response.status_code}: {error_message}"
            )

    def get_available_models(self) -> List[str]:
        """
        获取支持的模型列表

        Returns:
            模型名称列表
        """
        return self.SUPPORTED_MODELS.copy()

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            True if valid, False otherwise
        """
        # API密钥必须存在且不为空
        if not self.config.api_key or len(self.config.api_key.strip()) == 0:
            return False

        # 模型名称必须在支持列表中
        if self.config.model not in self.SUPPORTED_MODELS:
            return False

        # base_url必须是有效的URL
        if self.config.base_url:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

            if not url_pattern.match(self.config.base_url):
                return False

        return True

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量

        使用混合估算策略：
        - 英文/数字/符号: ~4字符 = 1 token
        - 中文/日文/韩文: ~1.5字符 = 1 token

        Args:
            text: 要估算的文本

        Returns:
            估算的token数量
        """
        if not text:
            return 0

        # 统计中文字符数量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

        # 统计其他字符数量
        other_chars = len(text) - chinese_chars

        # 混合估算
        # 中文: 1.5字符/token
        # 英文: 4字符/token
        chinese_tokens = chinese_chars / 1.5
        other_tokens = other_chars / 4.0

        total_tokens = int(chinese_tokens + other_tokens)

        return max(total_tokens, 1)  # 至少1个token

    async def close(self):
        """
        关闭HTTP客户端连接
        """
        await self.client.aclose()

    def __del__(self):
        """
        析构函数：确保客户端关闭
        """
        try:
            import asyncio
            asyncio.create_task(self.close())
        except:
            pass
