# -*- coding: utf-8 -*-
"""
OpenAI Provider Implementation
OpenAI API 的具体实现（也兼容 OpenAI-compatible 端点）
"""

import json
import time
import logging
from typing import List, Iterator, Optional, Dict, Any
import requests
from .base_provider import (
    BaseProvider, ProviderConfig, ChatMessage, ChatResponse,
    ProviderType, ProviderError, RateLimitError, AuthenticationError,
    NetworkError, InvalidRequestError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """
    OpenAI API 提供商实现
    支持 OpenAI 官方 API 以及兼容的第三方端点
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, config: ProviderConfig):
        """初始化 OpenAI 提供商"""
        super().__init__(config)
        self.provider_type = ProviderType.OPENAI
        self.base_url = config.base_url or self.DEFAULT_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
        }

    def validate_connection(self) -> tuple[bool, str]:
        """
        验证 OpenAI API 连接

        Returns:
            (是否成功, 消息)
        """
        try:
            # 使用 models 端点测试连接
            url = f"{self.base_url}/models"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                models = response.json().get('data', [])
                model_count = len(models)
                return True, f"连接成功 ✓ (发现 {model_count} 个可用模型)"
            elif response.status_code == 401:
                return False, "认证失败：API Key 无效"
            else:
                return False, f"连接失败：HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "连接超时：请检查网络或 API 端点"
        except requests.exceptions.ConnectionError:
            return False, "网络错误：无法连接到 API 端点"
        except Exception as e:
            return False, f"未知错误：{str(e)}"

    def send_message(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """
        发送非流式消息

        Args:
            messages: 消息列表
            stream: 必须为 False（流式请使用 stream_message）
            system_prompt: 系统提示词

        Returns:
            ChatResponse 对象

        Raises:
            ProviderError: API 调用失败
        """
        if stream:
            raise InvalidRequestError("流式响应请使用 stream_message 方法")

        # 构建消息列表
        message_list = self._build_message_list(messages, system_prompt)

        # 构建请求体
        payload = {
            'model': self.config.model,
            'messages': message_list,
        }

        if self.config.temperature is not None:
            payload['temperature'] = self.config.temperature
        if self.config.max_tokens is not None:
            payload['max_tokens'] = self.config.max_tokens
        if self.config.top_p is not None:
            payload['top_p'] = self.config.top_p
        if self.config.frequency_penalty is not None:
            payload['frequency_penalty'] = self.config.frequency_penalty
        if self.config.presence_penalty is not None:
            payload['presence_penalty'] = self.config.presence_penalty

        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout
            )

            self._check_response_status(response)

            data = response.json()
            return self._parse_response(data)

        except requests.exceptions.Timeout:
            raise NetworkError("请求超时", status_code=408)
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"网络连接失败: {str(e)}")
        except json.JSONDecodeError:
            raise ProviderError("API 返回了无效的 JSON 数据")

    def stream_message(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        """
        发送流式消息

        Args:
            messages: 消息列表
            system_prompt: 系统提示词

        Yields:
            str: 响应文本片段

        Raises:
            ProviderError: API 调用失败
        """
        message_list = self._build_message_list(messages, system_prompt)

        payload = {
            'model': self.config.model,
            'messages': message_list,
            'stream': True,
        }
        if self.config.temperature is not None:
            payload['temperature'] = self.config.temperature
        if self.config.max_tokens is not None:
            payload['max_tokens'] = self.config.max_tokens
        if self.config.top_p is not None:
            payload['top_p'] = self.config.top_p
        if self.config.frequency_penalty is not None:
            payload['frequency_penalty'] = self.config.frequency_penalty
        if self.config.presence_penalty is not None:
            payload['presence_penalty'] = self.config.presence_penalty

        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.config.timeout
            )

            self._check_response_status(response)

            # 解析 SSE 流
            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode('utf-8')

                # SSE 格式: "data: {...}"
                if line.startswith('data: '):
                    data_str = line[6:]  # 移除 "data: " 前缀

                    # 流结束标记
                    if data_str == '[DONE]':
                        break

                    try:
                        data = json.loads(data_str)

                        # usage 信息块（choices 为空数组）
                        if not data.get('choices'):
                            usage = data.get('usage')
                            if usage:
                                yield {
                                    'type': 'usage',
                                    'payload': usage
                                }
                            # 其他非 usage 元数据忽略
                            continue

                        # 安全地获取第一个 choice
                        choice = data['choices'][0]
                        delta = choice.get('delta', {})
                        content = delta.get('content', '')

                        if content:
                            yield {
                                'type': 'delta',
                                'payload': content
                            }

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"解析流式响应失败: {e}, line: {line}")
                        continue

        except requests.exceptions.Timeout:
            raise NetworkError("流式请求超时", status_code=408)
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"流式连接失败: {str(e)}")

    def estimate_tokens(self, text: str) -> int:
        """
        粗略估算 token 数量（按字符数估算）
        实际项目应使用 tiktoken 库精确计算

        Args:
            text: 文本内容

        Returns:
            估算的 token 数
        """
        # 粗略估算：英文约 4 字符/token，中文约 1.5 字符/token
        # 这里采用保守估算
        return len(text) // 3

    def _build_message_list(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str]
    ) -> List[Dict[str, str]]:
        """
        构建 OpenAI 格式的消息列表

        Args:
            messages: ChatMessage 列表
            system_prompt: 系统提示词

        Returns:
            字典格式的消息列表
        """
        message_list = []

        # 添加系统提示词（如果提供）
        if system_prompt:
            message_list.append({
                'role': 'system',
                'content': system_prompt
            })

        # 添加对话历史
        for msg in messages:
            message_list.append(msg.to_dict())

        return message_list

    def _check_response_status(self, response: requests.Response):
        """
        检查响应状态码并抛出相应异常

        Args:
            response: requests 响应对象

        Raises:
            ProviderError: 各种 API 错误
        """
        if response.status_code == 200:
            return

        try:
            error_data = response.json().get('error', {})
            error_message = error_data.get('message', '未知错误')
        except:
            error_message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(
                f"认证失败: {error_message}",
                status_code=401
            )
        elif response.status_code == 429:
            raise RateLimitError(
                f"速率限制: {error_message}",
                status_code=429
            )
        elif response.status_code == 400:
            raise InvalidRequestError(
                f"无效请求: {error_message}",
                status_code=400
            )
        elif response.status_code >= 500:
            raise ProviderError(
                f"服务器错误: {error_message}",
                status_code=response.status_code
            )
        else:
            raise ProviderError(
                f"API 错误: {error_message}",
                status_code=response.status_code
            )

    def _parse_response(self, data: Dict[str, Any]) -> ChatResponse:
        """
        解析 OpenAI API 响应

        Args:
            data: API 返回的 JSON 数据

        Returns:
            ChatResponse 对象

        Raises:
            ProviderError: 解析失败
        """
        try:
            choice = data['choices'][0]
            content = choice['message']['content']
            finish_reason = choice.get('finish_reason')

            usage = data.get('usage', {})

            return ChatResponse(
                content=content,
                model=data.get('model', self.config.model),
                finish_reason=finish_reason,
                usage=usage,
                metadata={'raw_response': data}
            )
        except (KeyError, IndexError) as e:
            raise ProviderError(f"解析响应失败: {e}, data: {data}")
