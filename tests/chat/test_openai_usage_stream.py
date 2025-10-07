#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for OpenAIProvider stream usage parsing."""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.ai_integration.api_providers.openai_provider import OpenAIProvider
from modules.ai_integration.api_providers.base_provider import ProviderConfig, ChatMessage


class MockStreamResponse:
    def __init__(self, lines):
        self._lines = lines
        self.status_code = 200

    def iter_lines(self):
        for line in self._lines:
            yield line.encode("utf-8")


def test_stream_message_emits_usage_event():
    payload_lines = [
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,"model":"gpt","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}' ,
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,"model":"gpt","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}',
        'data: [DONE]'
    ]

    config = ProviderConfig(api_key="dummy", base_url="https://api.example.com", model="gpt-test")
    provider = OpenAIProvider(config)

    with patch("modules.ai_integration.api_providers.openai_provider.requests.post") as mock_post:
        mock_post.return_value = MockStreamResponse(payload_lines)

        iterator = provider.stream_message([ChatMessage(role='user', content='hi')])
        events = list(iterator)

    assert events[0]['type'] == 'delta'
    assert events[0]['payload'] == '你好'
    assert events[1]['type'] == 'usage'
    assert events[1]['payload']['prompt_tokens'] == 10
    assert events[1]['payload']['total_tokens'] == 15
