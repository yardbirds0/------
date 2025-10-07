import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from controllers.request_preview_service import RequestPreviewService
from modules.ai_integration.api_providers.base_provider import ChatMessage
from models.data_models import PromptTemplate


def create_prompt(content: str = "You are helper.", title: str = "Helper") -> PromptTemplate:
    prompt = PromptTemplate()
    prompt.content = content
    prompt.title = title
    prompt.group_name = "默认提示词"
    prompt.updated_at = datetime.now()
    return prompt


def test_update_sources_returns_none_when_no_content() -> None:
    service = RequestPreviewService()

    assert service.update_sources() is None

    service.set_headers({"Authorization": "Bearer 1234567890abcdef"})
    state = service.update_sources()
    assert state is not None
    assert state.masked_headers["Authorization"].endswith("cdef")


def test_update_sources_generates_state_with_masked_headers() -> None:
    service = RequestPreviewService()
    service.set_headers({"Authorization": "Bearer 1234567890abcdef"})

    state = service.update_sources(
        parameters={"model": "gpt-test", "temperature": 0.2},
        prompt=create_prompt("Stay helpful"),
        history=[ChatMessage(role="user", content="Hello")],
        draft_text="Working draft",
    )

    assert state is not None
    assert "Bearer 123456******cdef" in state.display_text
    parsed = json.loads(state.display_text)
    assert parsed["payload"]["model"] == "gpt-test"
    assert parsed["payload"]["temperature"] == 0.2
    assert parsed["payload"]["draft_included"] is True
    assert "parameters" not in parsed["payload"]
    assert "prompt_title" not in parsed["payload"]
    assert "prompt_group" not in parsed["payload"]
    # raw text should contain the full token
    assert "Bearer 1234567890abcdef" in state.raw_text


def test_update_sources_suppresses_duplicate_states() -> None:
    service = RequestPreviewService()
    service.set_headers({"Authorization": "Bearer ABCDEFGHIJK"})

    first = service.update_sources(
        parameters={"model": "gpt"},
        history=[ChatMessage(role="user", content="Hi")],
    )
    assert first is not None

    # identical update should return None
    assert service.update_sources(parameters={"model": "gpt"}, history=[ChatMessage(role="user", content="Hi")]) is None


def test_build_preview_uses_override_messages() -> None:
    service = RequestPreviewService()
    service.set_headers({"Authorization": "Bearer tokenvalue"})
    service.update_sources(parameters={"model": "gpt"}, prompt=create_prompt())

    request_payload = {
        "url": "https://api.example.com/v1/chat",
        "model": "gpt",
        "messages": [
            {"role": "system", "content": "Stay helpful"},
            {"role": "user", "content": "Hello"},
        ],
        "system_prompt": None,
        "system_prompt_combined": "",
        "temperature": None,
        "max_tokens": None,
        "top_p": None,
        "frequency_penalty": None,
        "presence_penalty": None,
        "stream": True,
        "draft_included": False,
    }

    state = service.build_preview(request_payload=request_payload)
    assert state is not None
    parsed = json.loads(state.display_text)
    assert parsed["payload"]["messages"][0]["role"] == "system"
    assert parsed["payload"]["draft_included"] is False


def test_mark_request_sent_clears_draft() -> None:
    service = RequestPreviewService()
    service.update_sources(
        parameters={"model": "gpt"},
        history=[ChatMessage(role="user", content="Hi")],
        draft_text="typing...",
    )

    snapshot = service.mark_request_sent()
    assert snapshot is not None
    parsed = json.loads(snapshot.display_text)
    assert parsed["payload"]["draft_included"] is False


def test_placeholder_state_contains_base_structure() -> None:
    service = RequestPreviewService()
    placeholder = service.placeholder_state()
    parsed = json.loads(placeholder.display_text)
    assert "url" in parsed["payload"]
    assert parsed["payload"]["model"] != ""
