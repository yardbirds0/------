from __future__ import annotations

"""Utilities for constructing request preview payloads for the debug tab."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import json

from modules.ai_integration.api_providers.base_provider import ChatMessage
from models.data_models import PromptTemplate


@dataclass
class RequestPreviewState:
    """Immutable snapshot returned to the UI layer."""

    masked_headers: Dict[str, Any]
    payload: Dict[str, Any]
    display_text: str
    is_placeholder: bool
    last_updated: datetime
    raw_text: Optional[str] = None
    raw_headers: Optional[Dict[str, Any]] = None


class RequestPreviewService:
    """Collects request related data and produces debug view snapshots."""

    _SENSITIVE_HEADER_KEYS = {
        "authorization",
        "api-key",
        "x-api-key",
        "api_key",
        "bearer",
        "token",
        "secret",
    }

    def __init__(self) -> None:
        self._raw_headers: Dict[str, Any] = {}
        self._parameters: Dict[str, Any] = {}
        self._prompt: Optional[PromptTemplate] = None
        self._history: List[ChatMessage] = []
        self._draft_text: str = ""
        self._last_display: Optional[str] = None
        self._endpoint_url: str = "https://api.openai.com/v1/chat/completions"
        self._model_name: str = "unknown"
        self._system_prompt: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_headers(self, headers: Optional[Dict[str, Any]]) -> None:
        """Stores provider headers, replacing existing values."""

        self._raw_headers = dict(headers or {})
        self._invalidate_cache()

    def set_request_metadata(
        self,
        *,
        endpoint_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        if endpoint_url:
            self._endpoint_url = endpoint_url
        if model_name:
            self._model_name = model_name
        self._invalidate_cache()

    def update_sources(
        self,
        *,
        parameters: Optional[Dict[str, Any]] = None,
        prompt: Optional[PromptTemplate] = None,
        history: Optional[Iterable[ChatMessage]] = None,
        draft_text: Optional[str] = None,
    ) -> Optional[RequestPreviewState]:
        """Updates internal caches and returns a new preview state when changed."""

        if parameters is not None:
            self._parameters = dict(parameters)
            if parameters.get("model"):
                self._model_name = str(parameters.get("model"))
            self._system_prompt = parameters.get("system_prompt") if "system_prompt" in parameters else None
        if prompt is not None:
            self._prompt = prompt
        if history is not None:
            self._history = list(history)
        if draft_text is not None:
            self._draft_text = draft_text

        state = self._build_state(include_draft=True)
        if state is None:
            return None

        if state.display_text == self._last_display:
            return None

        self._last_display = state.display_text
        return state

    def build_preview(self, *, request_payload: Dict[str, Any]) -> RequestPreviewState:
        """Builds a snapshot using the actual payload dispatched to the API."""

        masked_headers = self._mask_headers(self._raw_headers)
        masked_dict = {"headers": masked_headers, "payload": request_payload}
        raw_dict = {"headers": self._raw_headers, "payload": request_payload}

        state = RequestPreviewState(
            masked_headers=masked_headers,
            payload=request_payload,
            display_text=self._safe_json_dumps(masked_dict),
            raw_text=self._safe_json_dumps(raw_dict),
            raw_headers=dict(self._raw_headers),
            is_placeholder=False,
            last_updated=datetime.now(),
        )

        self._last_display = state.display_text
        return state

    def mark_request_sent(self) -> Optional[RequestPreviewState]:
        """Clears transient draft text after a request has been dispatched."""

        if not self._draft_text:
            return None

        self._draft_text = ""
        state = self._build_state(include_draft=False)
        if state is None:
            return None

        if state.display_text == self._last_display:
            return None

        self._last_display = state.display_text
        return state

    def placeholder_state(self) -> RequestPreviewState:
        """Returns a placeholder snapshot for UI initialization."""

        return self._placeholder_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_state(
        self,
        *,
        include_draft: bool,
        messages_override: Optional[List[ChatMessage]] = None,
    ) -> Optional[RequestPreviewState]:
        has_prompt = bool(self._prompt and (self._prompt.content or self._prompt.title))
        has_history = bool(self._history)
        has_parameters = bool(self._parameters)
        has_draft = bool(self._draft_text.strip())

        if not any([has_prompt, has_history, has_parameters, has_draft, self._raw_headers]):
            return None

        masked_headers = self._mask_headers(self._raw_headers)

        payload = self._compose_payload(
            messages_override=messages_override,
            include_draft=include_draft,
        )

        raw_dict = {
            "headers": self._raw_headers,
            "payload": payload,
        }
        masked_dict = {
            "headers": masked_headers,
            "payload": payload,
        }

        display_text = self._safe_json_dumps(masked_dict)
        raw_text = self._safe_json_dumps(raw_dict)

        return RequestPreviewState(
            masked_headers=masked_headers,
            payload=payload,
            display_text=display_text,
            raw_text=raw_text,
            raw_headers=dict(self._raw_headers),
            is_placeholder=False,
            last_updated=datetime.now(),
        )

    def _compose_payload(
        self,
        *,
        messages_override: Optional[List[ChatMessage]],
        include_draft: bool,
    ) -> Dict[str, Any]:
        parameters = self._filter_parameters(self._parameters)
        developer_prompt = (self._prompt.content or "") if self._prompt else ""

        if messages_override is not None:
            messages = [msg.to_dict() for msg in messages_override]
        else:
            messages = [msg.to_dict() for msg in self._history]
            if include_draft and self._draft_text.strip():
                messages.append(
                    {
                        "role": "user",
                        "content": self._draft_text,
                        "metadata": {"draft": True},
                    }
                )

        base_system_prompt = self._system_prompt
        system_prompt_for_api = base_system_prompt

        if developer_prompt:
            combined_prompt = developer_prompt
            if base_system_prompt:
                combined_prompt = f"{base_system_prompt}\n\n{developer_prompt}".strip()
            system_prompt_for_api = base_system_prompt if base_system_prompt else None
            if not messages_override:
                messages = [
                    ChatMessage(role="system", content=combined_prompt).to_dict()
                ] + messages

        payload: Dict[str, Any] = {
            "url": self._endpoint_url,
            "model": parameters.get("model", self._model_name),
            "messages": messages,
            "draft_included": include_draft and bool(self._draft_text.strip()),
        }

        if system_prompt_for_api:
            payload["system_prompt"] = system_prompt_for_api

        optional_fields = [
            "temperature",
            "max_tokens",
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stream",
        ]
        for field in optional_fields:
            if field in parameters:
                payload[field] = parameters[field]

        return payload

    def _mask_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        masked: Dict[str, Any] = {}
        for key, value in headers.items():
            if value is None:
                masked[key] = value
                continue

            value_str = str(value)
            if self._is_sensitive_key(key) or self._contains_token_like(value_str):
                masked[key] = self._mask_sensitive_value(value_str)
            else:
                masked[key] = value
        return masked

    def _mask_sensitive_value(self, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            return value

        prefix = ""
        core = stripped
        lowered = stripped.lower()
        if lowered.startswith("bearer "):
            prefix = stripped[:7]
            core = stripped[7:]

        masked_core = self._mask_core(core)
        return f"{prefix}{masked_core}" if prefix else masked_core

    def _mask_core(self, value: str) -> str:
        length = len(value)
        if length <= 4:
            return "*" * length
        if length <= 10:
            return f"{value[:2]}{'*' * (length - 4)}{value[-2:]}"
        return f"{value[:6]}{'*' * (length - 10)}{value[-4:]}"

    def _filter_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in parameters.items():
            if key in {"api_key", "apiKey", "secret"}:
                continue
            sanitized[key] = value
        return sanitized

    def _safe_json_dumps(self, data: Dict[str, Any]) -> str:
        def _default(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, PromptTemplate):
                return obj.to_dict()
            if isinstance(obj, ChatMessage):
                return obj.to_dict()
            return str(obj)

        return json.dumps(data, ensure_ascii=False, indent=2, default=_default)

    def _contains_token_like(self, value: str) -> bool:
        lowered = value.lower()
        return any(token in lowered for token in self._SENSITIVE_HEADER_KEYS)

    def _is_sensitive_key(self, key: str) -> bool:
        return key.lower() in self._SENSITIVE_HEADER_KEYS

    def _placeholder_state(self) -> RequestPreviewState:
        default_headers = self._raw_headers or {
            "Content-Type": "application/json",
            "Authorization": "Bearer <api-key>"
        }
        masked_headers = self._mask_headers(default_headers)
        payload = self._compose_payload(messages_override=[], include_draft=False)
        masked_dict = {"headers": masked_headers, "payload": payload}
        raw_dict = {"headers": default_headers, "payload": payload}

        return RequestPreviewState(
            masked_headers=masked_headers,
            payload=payload,
            display_text=self._safe_json_dumps(masked_dict),
            raw_text=self._safe_json_dumps(raw_dict),
            raw_headers=default_headers,
            is_placeholder=False,
            last_updated=datetime.now(),
        )

    def _invalidate_cache(self) -> None:
        self._last_display = None
