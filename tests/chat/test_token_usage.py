#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for TokenUsageInfo helper."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models.data_models import TokenUsageInfo


def test_token_usage_from_payload_complete():
    payload = {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}

    info = TokenUsageInfo.from_usage_payload(payload)

    assert info.status == "complete"
    assert info.prompt_tokens == 12
    assert info.completion_tokens == 8
    assert info.total_tokens == 20
    assert info.as_text() == "输入：12；输出：8，总：20"


def test_token_usage_from_payload_missing_returns_placeholder():
    info = TokenUsageInfo.from_usage_payload(None)
    assert info.status == "missing"
    assert info.as_text() == TokenUsageInfo.PLACEHOLDER_TEXT


def test_token_usage_metadata_roundtrip():
    original = TokenUsageInfo(
        prompt_tokens=5,
        completion_tokens=7,
        total_tokens=12,
        status="complete",
        recorded_at=datetime.now(),
    )

    metadata = {"token_usage": original.to_metadata()}
    restored = TokenUsageInfo.from_metadata(metadata.get("token_usage"))

    assert restored.status == "complete"
    assert restored.prompt_tokens == 5
    assert restored.completion_tokens == 7
    assert restored.total_tokens == 12


def test_token_usage_metadata_incomplete_returns_placeholder():
    metadata = {"token_usage": {"prompt_tokens": 3}}
    info = TokenUsageInfo.from_metadata(metadata.get("token_usage"))

    assert info.status == "missing"
    assert info.as_text() == TokenUsageInfo.PLACEHOLDER_TEXT
