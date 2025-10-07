#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Connection Testing Service
用于测试AI Provider的API连接是否正常
"""

import requests
from typing import Optional
from PySide6.QtCore import QObject, Signal, QThread


class APITestWorker(QObject):
    """
    API测试Worker，运行在独立线程中

    Signals:
        progress_update(str, int, int): 进度更新 (message, current_attempt, max_attempts)
        test_finished(bool, str): 测试完成 (success, message)
    """

    # 信号定义
    progress_update = Signal(str, int, int)  # message, current_attempt, max_attempts
    test_finished = Signal(bool, str)  # success, message

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_id: str,
        max_retries: int = 3,
        timeout: int = 10,
        parent: Optional[QObject] = None,
    ):
        """
        初始化API测试Worker

        Args:
            api_url: API端点URL
            api_key: API密钥
            model_id: 模型ID
            max_retries: 最大重试次数（默认3次）
            timeout: 单次请求超时时间（秒，默认10秒）
            parent: 父对象
        """
        super().__init__(parent)

        self.api_url = api_url
        self.api_key = api_key
        self.model_id = model_id
        self.max_retries = max_retries
        self.timeout = timeout

    def test_connection(self):
        """
        执行API连接测试

        发送简单的"hi"消息到API端点，验证连接是否正常
        """
        # 构建请求数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 10,
        }

        # 确保URL以/chat/completions结尾
        url = self.api_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        # 重试逻辑
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            # 发送进度更新
            self.progress_update.emit(
                f"正在测试连接... ({attempt}/{self.max_retries})",
                attempt,
                self.max_retries,
            )

            try:
                # 发送HTTP请求
                response = requests.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )

                # 检查响应状态
                if response.status_code == 200:
                    # 成功
                    self.test_finished.emit(True, "连接成功！API配置正确。")
                    return
                elif response.status_code == 401:
                    # 认证失败
                    self.test_finished.emit(False, "认证失败：API密钥无效或已过期。")
                    return
                elif response.status_code == 404:
                    # 端点未找到
                    self.test_finished.emit(
                        False, f"端点未找到：{url}\n请检查API地址是否正确。"
                    )
                    return
                else:
                    # 其他错误状态码
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"

            except requests.exceptions.Timeout:
                last_error = f"请求超时（超过{self.timeout}秒）"

            except requests.exceptions.ConnectionError as e:
                last_error = f"连接错误：{str(e)[:100]}"

            except requests.exceptions.RequestException as e:
                last_error = f"请求异常：{str(e)[:100]}"

            except Exception as e:
                last_error = f"未知错误：{str(e)[:100]}"

        # 所有重试都失败
        self.test_finished.emit(
            False,
            f"连接失败（{self.max_retries}次尝试后）\n\n最后错误：\n{last_error}",
        )


class APITestService(QObject):
    """
    API测试服务（单例模式）

    管理QThread和Worker的生命周期，提供简单的测试API

    Signals:
        progress_update(str, int, int): 进度更新（转发自Worker）
        test_finished(bool, str): 测试完成（转发自Worker）
    """

    _instance: Optional["APITestService"] = None

    # 信号定义
    progress_update = Signal(str, int, int)  # message, current_attempt, max_attempts
    test_finished = Signal(bool, str)  # success, message

    @classmethod
    def instance(cls) -> "APITestService":
        """
        获取单例实例

        Returns:
            APITestService: 单例实例
        """
        if cls._instance is None:
            cls._instance = APITestService()
        return cls._instance

    def __init__(self):
        """初始化API测试服务（私有，使用instance()获取）"""
        if APITestService._instance is not None:
            raise RuntimeError(
                "APITestService is a singleton. Use APITestService.instance() instead."
            )

        super().__init__()

        self.thread: Optional[QThread] = None
        self.worker: Optional[APITestWorker] = None

    def test_api(
        self,
        api_url: str,
        api_key: str,
        model_id: str,
        max_retries: int = 3,
        timeout: int = 10,
    ):
        """
        测试API连接

        Args:
            api_url: API端点URL
            api_key: API密钥
            model_id: 模型ID
            max_retries: 最大重试次数（默认3次）
            timeout: 单次请求超时时间（秒，默认10秒）
        """
        # 如果已有测试在运行，先清理
        if self.thread is not None and self.thread.isRunning():
            self._cleanup_worker()

        # 创建新线程
        self.thread = QThread()

        # 创建Worker
        self.worker = APITestWorker(
            api_url=api_url,
            api_key=api_key,
            model_id=model_id,
            max_retries=max_retries,
            timeout=timeout,
        )

        # 将Worker移到线程
        self.worker.moveToThread(self.thread)

        # 连接信号
        self.thread.started.connect(self.worker.test_connection)
        self.worker.progress_update.connect(self.progress_update.emit)
        self.worker.test_finished.connect(self._on_test_finished)

        # 启动线程
        self.thread.start()

    def _on_test_finished(self, success: bool, message: str):
        """
        测试完成处理

        Args:
            success: 是否成功
            message: 结果消息
        """
        # 转发信号
        self.test_finished.emit(success, message)

        # 清理资源
        self._cleanup_worker()

    def _cleanup_worker(self):
        """清理Worker和线程资源"""
        if self.thread is not None:
            # 停止线程
            self.thread.quit()
            self.thread.wait(2000)  # 等待2秒

            # 如果线程还在运行，强制终止
            if self.thread.isRunning():
                self.thread.terminate()
                self.thread.wait()

            # 清理对象
            if self.worker is not None:
                self.worker.deleteLater()
                self.worker = None

            self.thread.deleteLater()
            self.thread = None
