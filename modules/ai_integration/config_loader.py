# -*- coding: utf-8 -*-
"""
AI Configuration Loader
AI服务配置加载器，支持JSON配置文件的读写和默认配置
"""

import json
from pathlib import Path
from typing import Dict, Optional
from .exceptions import AIServiceError


class AIConfigLoader:
    """
    AI服务配置加载器

    功能：
    - 加载JSON配置文件
    - 保存配置到JSON
    - 提供默认配置（内置Gemini转发配置）
    - 配置验证
    - 多服务支持（OpenAI、Claude、Gemini等）
    """

    DEFAULT_CONFIG_PATH = "config/ai_services.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径（默认: config/ai_services.json）
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)

    def load_config(self) -> Dict:
        """
        加载AI服务配置

        如果配置文件不存在，返回默认配置并创建配置文件

        Returns:
            配置字典

        Raises:
            AIServiceError: 配置文件格式错误
        """
        # 配置文件不存在，使用默认配置
        if not self.config_path.exists():
            print(f"[WARN]  Config file not found: {self.config_path}")
            print(f"[OK] Using default configuration (Gemini 2.5 Pro)")

            default_config = self.get_default_config()

            # 创建并保存默认配置
            try:
                self.save_config(default_config)
                print(f"[OK] Default config saved to: {self.config_path}")
            except Exception as e:
                print(f"[WARN]  Failed to save default config: {e}")

            return default_config

        # 加载配置文件
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"[OK] Config loaded from: {self.config_path}")
            return config

        except json.JSONDecodeError as e:
            raise AIServiceError(
                f"Invalid JSON in config file {self.config_path}: {str(e)}"
            )
        except Exception as e:
            raise AIServiceError(
                f"Failed to load config from {self.config_path}: {str(e)}"
            )

    def save_config(self, config: Dict):
        """
        保存配置到JSON文件

        Args:
            config: 配置字典

        Raises:
            AIServiceError: 保存失败
        """
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[OK] Config saved to: {self.config_path}")

        except Exception as e:
            raise AIServiceError(
                f"Failed to save config to {self.config_path}: {str(e)}"
            )

    @staticmethod
    def get_default_config() -> Dict:
        """
        获取默认配置

        默认使用Gemini 2.5 Pro（通过转发服务）

        Returns:
            默认配置字典，包含：
            - active_service: 当前激活的服务
            - services: 各AI服务的配置
        """
        return {
            "active_service": "openai",
            "services": {
                "openai": {
                    "api_key": "UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
                    "base_url": "https://api.kkyyxx.xyz/v1",
                    "model": "gemini-2.5-pro",
                    "timeout": 30,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "description": "Gemini 2.5 Pro (via OpenAI-compatible forwarding)"
                },
                "openai_official": {
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4-turbo",
                    "timeout": 30,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "description": "OpenAI Official API (requires your own API key)"
                },
                "claude": {
                    "api_key": "",
                    "base_url": "",
                    "model": "claude-3-opus",
                    "timeout": 30,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "description": "Anthropic Claude (requires configuration)"
                }
            },
            "metadata": {
                "version": "1.0.0",
                "created_at": "2025-01-10",
                "description": "AI服务配置文件 - 支持多种AI服务提供商"
            }
        }

    def get_service_config(
        self,
        service_name: Optional[str] = None
    ) -> Dict:
        """
        获取指定服务的配置

        Args:
            service_name: 服务名称（如'openai'），None则使用active_service

        Returns:
            服务配置字典

        Raises:
            AIServiceError: 服务不存在或配置无效
        """
        config = self.load_config()

        # 确定要使用的服务
        target_service = service_name or config.get('active_service', 'openai')

        # 检查服务是否存在
        if 'services' not in config:
            raise AIServiceError("Invalid config: missing 'services' section")

        if target_service not in config['services']:
            available = ', '.join(config['services'].keys())
            raise AIServiceError(
                f"Service '{target_service}' not found in config. "
                f"Available services: {available}"
            )

        service_config = config['services'][target_service]

        # 验证必需字段
        required_fields = ['api_key', 'model']
        for field in required_fields:
            if field not in service_config:
                raise AIServiceError(
                    f"Invalid config for '{target_service}': missing '{field}'"
                )

        return service_config

    def set_active_service(self, service_name: str):
        """
        设置激活的AI服务

        Args:
            service_name: 服务名称

        Raises:
            AIServiceError: 服务不存在
        """
        config = self.load_config()

        if 'services' not in config or service_name not in config['services']:
            available = ', '.join(config.get('services', {}).keys())
            raise AIServiceError(
                f"Service '{service_name}' not found. "
                f"Available services: {available}"
            )

        config['active_service'] = service_name
        self.save_config(config)

        print(f"[OK] Active service set to: {service_name}")

    def update_service_config(
        self,
        service_name: str,
        updates: Dict
    ):
        """
        更新指定服务的配置

        Args:
            service_name: 服务名称
            updates: 要更新的配置项

        Raises:
            AIServiceError: 服务不存在
        """
        config = self.load_config()

        if 'services' not in config or service_name not in config['services']:
            raise AIServiceError(f"Service '{service_name}' not found")

        # 更新配置
        config['services'][service_name].update(updates)

        # 保存配置
        self.save_config(config)

        print(f"[OK] Service '{service_name}' config updated")

    def list_services(self) -> Dict[str, str]:
        """
        列出所有可用的AI服务

        Returns:
            服务名称到描述的映射 {"service_name": "description"}
        """
        config = self.load_config()

        services = {}
        for name, service_config in config.get('services', {}).items():
            description = service_config.get('description', 'No description')
            services[name] = description

        return services

    def validate_config(self, config: Dict) -> bool:
        """
        验证配置格式是否正确

        Args:
            config: 配置字典

        Returns:
            True if valid, False otherwise
        """
        # 检查必需的顶层字段
        if 'active_service' not in config:
            return False

        if 'services' not in config or not isinstance(config['services'], dict):
            return False

        # 检查active_service是否存在于services中
        if config['active_service'] not in config['services']:
            return False

        # 检查每个服务的配置
        for service_name, service_config in config['services'].items():
            # 必需字段
            required = ['api_key', 'model']
            for field in required:
                if field not in service_config:
                    return False

            # timeout必须是正整数
            if 'timeout' in service_config:
                timeout = service_config['timeout']
                if not isinstance(timeout, int) or timeout <= 0:
                    return False

        return True
