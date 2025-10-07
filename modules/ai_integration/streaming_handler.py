# -*- coding: utf-8 -*-
"""
Streaming Handler
处理 AI 流式响应的核心组件，使用 Qt 信号机制实现异步流式显示
"""

import logging
from typing import Iterator, Optional
from PySide6.QtCore import QObject, Signal, QThread
from .api_providers.base_provider import BaseProvider, ChatMessage

logger = logging.getLogger(__name__)


class StreamingHandler(QObject):
    """
    流式响应处理器
    在独立线程中处理 API 流式响应，通过信号通知 UI 更新
    """

    # 信号定义
    chunk_received = Signal(str)  # 接收到新的文本片段
    stream_started = Signal()  # 流式响应开始
    stream_finished = Signal(str)  # 流式响应完成（完整文本）
    stream_error = Signal(str)  # 流式响应出错
    usage_received = Signal(dict)  # 收到 usage 信息块

    def __init__(self, provider: BaseProvider):
        """
        初始化流式处理器

        Args:
            provider: LLM 服务提供商实例
        """
        super().__init__()
        self.provider = provider
        self.worker_thread: Optional[QThread] = None
        self.is_streaming = False
        self._full_response = ""
        self._last_usage: Optional[dict] = None

    def start_stream(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None
    ):
        """
        启动流式响应

        Args:
            messages: 消息历史
            system_prompt: 系统提示词
        """
        if self.is_streaming:
            logger.warning("已有流式响应在进行中，忽略新请求")
            return

        # 创建工作线程
        self.worker_thread = StreamWorker(
            self.provider,
            messages,
            system_prompt
        )

        # 连接信号
        self.worker_thread.chunk_received.connect(self._on_chunk_received)
        self.worker_thread.stream_finished.connect(self._on_stream_finished)
        self.worker_thread.stream_error.connect(self._on_stream_error)
        self.worker_thread.usage_received.connect(self._on_usage_received)

        # 启动线程
        self.is_streaming = True
        self._full_response = ""
        self._last_usage = None
        self.stream_started.emit()
        self.worker_thread.start()

    def cancel_stream(self):
        """取消当前流式响应"""
        if self.worker_thread and self.is_streaming:
            self.worker_thread.cancel()
            self.is_streaming = False
            logger.info("流式响应已取消")

    def _on_chunk_received(self, chunk: str):
        """
        处理接收到的文本片段

        Args:
            chunk: 文本片段
        """
        self._full_response += chunk
        self.chunk_received.emit(chunk)

    def _on_stream_finished(self):
        """处理流式响应完成"""
        self.is_streaming = False
        self.stream_finished.emit(self._full_response)
        logger.info(f"流式响应完成，总长度: {len(self._full_response)} 字符")

    def _on_stream_error(self, error_msg: str):
        """
        处理流式响应错误

        Args:
            error_msg: 错误消息
        """
        self.is_streaming = False
        self.stream_error.emit(error_msg)
        logger.error(f"流式响应错误: {error_msg}")

    def _on_usage_received(self, usage: dict):
        """处理 usage 信息块"""
        self._last_usage = usage or {}
        self.usage_received.emit(self._last_usage)

    @property
    def last_usage(self) -> Optional[dict]:
        """返回最近一次捕获的 usage 信息"""
        return self._last_usage


class StreamWorker(QThread):
    """
    流式响应工作线程
    在独立线程中调用 API，避免阻塞 UI
    """

    # 信号定义
    chunk_received = Signal(str)
    stream_finished = Signal()
    stream_error = Signal(str)
    usage_received = Signal(dict)

    def __init__(
        self,
        provider: BaseProvider,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None
    ):
        """
        初始化工作线程

        Args:
            provider: LLM 服务提供商
            messages: 消息列表
            system_prompt: 系统提示词
        """
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.system_prompt = system_prompt
        self._is_cancelled = False

    def run(self):
        """线程主函数"""
        try:
            # 调用流式 API
            stream_iterator = self.provider.stream_message(
                self.messages,
                self.system_prompt
            )

            # 逐个处理响应片段
            for event in stream_iterator:
                if self._is_cancelled:
                    break

                chunk: Optional[str] = None

                if isinstance(event, dict):
                    event_type = event.get('type')
                    if event_type == 'usage':
                        payload = event.get('payload') or {}
                        self.usage_received.emit(payload)
                        continue
                    elif event_type == 'delta':
                        chunk = event.get('payload', '')
                    else:
                        continue
                else:
                    chunk = event

                if chunk:
                    self.chunk_received.emit(chunk)

            if not self._is_cancelled:
                self.stream_finished.emit()

        except Exception as e:
            error_msg = f"流式响应失败: {str(e)}"
            logger.exception(error_msg)
            self.stream_error.emit(error_msg)

    def cancel(self):
        """取消流式响应"""
        self._is_cancelled = True
