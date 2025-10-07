# -*- coding: utf-8 -*-
"""
Prompt Store
管理提示词模板的加载与保存
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.data_models import PromptTemplate

logger = logging.getLogger(__name__)


class PromptStore:
    """管理全局默认提示词的存储"""

    DEFAULT_FILE = Path("config/prompt_templates.json")
    DEFAULT_KEY = "default_prompt"
    HISTORY_KEY = "history"
    MAX_HISTORY = 10

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_FILE
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._cached_template: Optional[PromptTemplate] = None
        self._cached_history: List[PromptTemplate] = []

    def load_default_prompt(self, force_reload: bool = False) -> PromptTemplate:
        """加载默认提示词"""
        if self._cached_template is not None and not force_reload:
            return self._cached_template

        if not self.config_path.exists():
            template = PromptTemplate()
            self.save_default_prompt(template)
            self._cached_template = template
            self._cached_history = []
            return template

        try:
            with open(self.config_path, "r", encoding="utf-8") as fp:
                data = json.load(fp) or {}
            prompt_data = data.get(self.DEFAULT_KEY, {})
            history_data = data.get(self.HISTORY_KEY, [])
            template = PromptTemplate.from_dict(prompt_data)
            history = [
                PromptTemplate.from_dict(item) for item in history_data if item
            ]
            self._cached_template = template
            self._cached_history = history
            return template
        except Exception as exc:  # noqa: BLE001
            logger.error("加载提示词文件失败: %s", exc)
            template = PromptTemplate()
            self._cached_template = template
            self._cached_history = []
            return template

    def save_default_prompt(self, template: PromptTemplate) -> None:
        """保存默认提示词"""
        history = self.get_history(force_reload=True)

        if self._cached_template:
            # 将旧模板加入历史
            previous = self._cached_template
            if previous.content != template.content or previous.title != template.title:
                history.insert(
                    0,
                    PromptTemplate(
                        group_name=previous.group_name,
                        title=previous.title,
                        content=previous.content,
                        updated_at=previous.updated_at,
                    ),
                )

        # 截断历史长度
        history = history[: self.MAX_HISTORY]

        payload = {
            self.DEFAULT_KEY: template.to_dict(),
            self.HISTORY_KEY: [item.to_dict() for item in history],
            "updated_at": datetime.now().isoformat(),
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2)
            self._cached_template = template
            self._cached_history = history
        except Exception as exc:  # noqa: BLE001
            logger.error("保存提示词文件失败: %s", exc)
            raise

    def get_history(self, limit: Optional[int] = None, force_reload: bool = False) -> List[PromptTemplate]:
        """获取默认提示词历史列表（按时间倒序）"""
        if force_reload or not self._cached_history:
            if not self.config_path.exists():
                self._cached_history = []
            else:
                try:
                    with open(self.config_path, "r", encoding="utf-8") as fp:
                        data = json.load(fp) or {}
                    history_data = data.get(self.HISTORY_KEY, [])
                    self._cached_history = [
                        PromptTemplate.from_dict(item) for item in history_data if item
                    ]
                except Exception as exc:  # noqa: BLE001
                    logger.error("读取提示词历史失败: %s", exc)
                    self._cached_history = []

        history = self._cached_history
        if limit is not None:
            return history[:limit]
        return history
