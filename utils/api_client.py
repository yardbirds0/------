#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Client Utility Tools
Handle HTTP requests and API communication
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib


class APIClient:
    """Generic API client with retry and caching capabilities"""

    def __init__(self, base_url: str = "", timeout: int = 30):
        """Initialize API client"""
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.last_request_time = None
        self.request_count = 0
        self.cache = {}  # Simple memory cache
        self.cache_ttl = 300  # 5 minutes cache TTL

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers for all requests"""
        self.session.headers.update(headers)

    def set_auth_token(self, token: str, auth_type: str = "Bearer") -> None:
        """Set authentication token"""
        self.session.headers["Authorization"] = f"{auth_type} {token}"

    def _generate_cache_key(self, method: str, url: str, data: Any = None) -> str:
        """Generate cache key for request"""
        key_data = f"{method}:{url}"
        if data:
            key_data += f":{json.dumps(data, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False

        timestamp = cache_entry.get("timestamp", 0)
        return (time.time() - timestamp) < self.cache_ttl

    def _cache_response(self, cache_key: str, response_data: Any) -> None:
        """Cache response data"""
        self.cache[cache_key] = {
            "data": response_data,
            "timestamp": time.time()
        }

    def get(self, endpoint: str, params: Optional[Dict] = None,
            use_cache: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """Make GET request"""
        return self.request("GET", endpoint, params=params, use_cache=use_cache)

    def post(self, endpoint: str, data: Optional[Dict] = None,
             json_data: Optional[Dict] = None,
             use_cache: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Make POST request"""
        return self.request("POST", endpoint, data=data, json_data=json_data, use_cache=use_cache)

    def request(self, method: str, endpoint: str,
                params: Optional[Dict] = None,
                data: Optional[Dict] = None,
                json_data: Optional[Dict] = None,
                use_cache: bool = False,
                max_retries: int = 3,
                retry_delay: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Make HTTP request with retry logic"""

        url = f"{self.base_url}{endpoint}" if not endpoint.startswith("http") else endpoint

        # Check cache first for GET requests
        if use_cache and method.upper() == "GET":
            cache_key = self._generate_cache_key(method, url, params)
            cache_entry = self.cache.get(cache_key)
            if self._is_cache_valid(cache_entry):
                return True, cache_entry["data"]

        # Prepare request parameters
        request_kwargs = {
            "timeout": self.timeout
        }

        if params:
            request_kwargs["params"] = params
        if data:
            request_kwargs["data"] = data
        if json_data:
            request_kwargs["json"] = json_data

        # Retry logic
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(method, url, **request_kwargs)
                self.last_request_time = datetime.now()
                self.request_count += 1

                if response.status_code == 200:
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        result = {"content": response.text}

                    # Cache successful GET responses
                    if use_cache and method.upper() == "GET":
                        cache_key = self._generate_cache_key(method, url, params)
                        self._cache_response(cache_key, result)

                    return True, result

                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    return False, {"error": error_msg, "status_code": response.status_code}

            except requests.exceptions.Timeout:
                last_exception = "Request timeout"
            except requests.exceptions.ConnectionError:
                last_exception = "Connection error"
            except requests.exceptions.RequestException as e:
                last_exception = f"Request exception: {str(e)}"
            except Exception as e:
                last_exception = f"Unexpected error: {str(e)}"

            # Wait before retry (except for last attempt)
            if attempt < max_retries:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff

        return False, {"error": last_exception}

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "cache_entries": len(self.cache),
            "session_headers": dict(self.session.headers)
        }

    def clear_cache(self) -> None:
        """Clear request cache"""
        self.cache.clear()

    def close(self) -> None:
        """Close session"""
        self.session.close()


class OpenAIAPIClient(APIClient):
    """Specialized OpenAI API client"""

    def __init__(self, api_key: str = "", model: str = "gpt-4-turbo", timeout: int = 30):
        """Initialize OpenAI API client"""
        super().__init__(base_url="https://api.openai.com/v1", timeout=timeout)

        self.model = model
        if api_key:
            self.set_auth_token(api_key)

        # Set default headers
        self.set_headers({
            "Content-Type": "application/json"
        })

    def chat_completion(self, messages: list, temperature: float = 0.1,
                       max_tokens: int = 2000, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Create chat completion"""

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        return self.post("/chat/completions", json_data=payload)

    def test_connection(self) -> Tuple[bool, str]:
        """Test OpenAI API connection"""
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, this is a connection test."}
        ]

        success, response = self.chat_completion(test_messages, max_tokens=50)

        if success:
            return True, "Connection successful"
        else:
            error_msg = response.get("error", "Unknown error")
            return False, error_msg


class RateLimiter:
    """Rate limiting utility"""

    def __init__(self, max_requests: int = 60, time_window: int = 60):
        """Initialize rate limiter"""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def can_make_request(self) -> bool:
        """Check if request can be made within rate limits"""
        now = time.time()

        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        return len(self.requests) < self.max_requests

    def record_request(self) -> None:
        """Record a request timestamp"""
        self.requests.append(time.time())

    def get_wait_time(self) -> float:
        """Get time to wait before next request"""
        if self.can_make_request():
            return 0.0

        if not self.requests:
            return 0.0

        oldest_request = min(self.requests)
        return self.time_window - (time.time() - oldest_request)

    def wait_if_needed(self) -> None:
        """Wait if rate limit exceeded"""
        wait_time = self.get_wait_time()
        if wait_time > 0:
            time.sleep(wait_time)


class RetryStrategy:
    """Retry strategy configuration"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 30.0, backoff_factor: float = 2.0):
        """Initialize retry strategy"""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        if attempt <= 0:
            return 0.0

        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if should retry based on attempt and error"""
        if attempt >= self.max_retries:
            return False

        # Retry on network errors, timeouts, and server errors
        if isinstance(error, (requests.exceptions.Timeout,
                             requests.exceptions.ConnectionError,
                             requests.exceptions.HTTPError)):
            return True

        # Don't retry on client errors (4xx)
        if hasattr(error, 'response') and error.response:
            if 400 <= error.response.status_code < 500:
                return False

        return True


def create_openai_client(api_key: str, model: str = "gpt-4-turbo") -> OpenAIAPIClient:
    """Create and configure OpenAI API client"""
    client = OpenAIAPIClient(api_key=api_key, model=model)
    return client


def format_messages_for_openai(system_prompt: str, user_content: str) -> list:
    """Format messages for OpenAI API"""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON data from AI response text"""
    try:
        # Try direct parsing first
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    import re

    # Look for ```json blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Look for any ``` blocks
    code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON-like structures
    json_patterns = [
        r'\{.*\}',  # Look for {...}
        r'\[.*\]'   # Look for [...]
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    return None