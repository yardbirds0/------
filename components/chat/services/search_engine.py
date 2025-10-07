# -*- coding: utf-8 -*-
"""
Provider/Model Search Engine
提供商/模型搜索引擎
"""

from typing import List, Dict, Tuple, Set


class SearchEngine:
    """
    Provider和Model搜索引擎

    功能：
    - 双重搜索：provider名称 + model名称/ID
    - 大小写不敏感的子串匹配
    - 实时过滤（优化性能 <100ms）
    """

    @staticmethod
    def search(
        query: str, providers: List[dict]
    ) -> Tuple[Set[str], Dict[str, List[str]]]:
        """
        搜索providers和models

        Args:
            query: 搜索查询字符串（大小写不敏感）
            providers: Provider列表，每个provider包含：
                - id: str
                - name: str
                - models: List[dict] with 'id' and 'name'

        Returns:
            Tuple包含：
            - matched_provider_ids: Set[str] - 匹配的provider ID集合
            - model_matches: Dict[provider_id: List[model_id]] - 每个provider下匹配的model IDs

        Example:
            >>> providers = [
            ...     {
            ...         "id": "openai",
            ...         "name": "OpenAI",
            ...         "models": [
            ...             {"id": "gpt-4", "name": "GPT-4"},
            ...             {"id": "gpt-3.5", "name": "GPT-3.5"}
            ...         ]
            ...     }
            ... ]
            >>> matched_providers, model_matches = SearchEngine.search("gpt", providers)
            >>> print(matched_providers)
            {'openai'}
            >>> print(model_matches)
            {'openai': ['gpt-4', 'gpt-3.5']}
        """
        # 空查询返回所有内容
        if not query or not query.strip():
            all_provider_ids = {p.get("id") for p in providers if p.get("id")}
            all_models = {}
            for provider in providers:
                provider_id = provider.get("id")
                if provider_id:
                    models = provider.get("models", [])
                    all_models[provider_id] = [
                        m.get("id") for m in models if m.get("id")
                    ]
            return all_provider_ids, all_models

        # 规范化查询（转小写）
        query_lower = query.strip().lower()

        matched_provider_ids: Set[str] = set()
        model_matches: Dict[str, List[str]] = {}

        # 遍历每个provider
        for provider in providers:
            provider_id = provider.get("id", "")
            provider_name = provider.get("name", "")
            models = provider.get("models", [])

            if not provider_id:
                continue

            # 检查provider名称是否匹配
            provider_name_matches = query_lower in provider_name.lower()

            # 检查models是否有匹配
            matched_model_ids: List[str] = []
            for model in models:
                model_id = model.get("id", "")
                model_name = model.get("name", "")

                # 匹配model ID或model名称
                if query_lower in model_id.lower() or query_lower in model_name.lower():
                    if model_id:
                        matched_model_ids.append(model_id)

            # 如果provider名称匹配，包含所有models
            if provider_name_matches:
                matched_provider_ids.add(provider_id)
                # Provider匹配时，返回所有models（即使model本身不匹配查询）
                model_matches[provider_id] = [m.get("id") for m in models if m.get("id")]
            # 如果有任何model匹配，也包含该provider
            elif matched_model_ids:
                matched_provider_ids.add(provider_id)
                model_matches[provider_id] = matched_model_ids

        return matched_provider_ids, model_matches

    @staticmethod
    def highlight_match(text: str, query: str) -> str:
        """
        生成带高亮标记的文本（用于UI显示）

        Args:
            text: 原始文本
            query: 搜索查询

        Returns:
            带<mark>标签的HTML字符串

        Example:
            >>> SearchEngine.highlight_match("OpenAI GPT-4", "gpt")
            'OpenAI <mark>GPT</mark>-4'
        """
        if not query or not query.strip():
            return text

        query_lower = query.strip().lower()
        text_lower = text.lower()

        # 找到所有匹配位置
        result = []
        last_end = 0

        while True:
            start_pos = text_lower.find(query_lower, last_end)
            if start_pos == -1:
                break

            # 添加匹配前的文本
            result.append(text[last_end:start_pos])

            # 添加高亮的匹配文本
            end_pos = start_pos + len(query_lower)
            result.append(f"<mark>{text[start_pos:end_pos]}</mark>")

            last_end = end_pos

        # 添加剩余文本
        result.append(text[last_end:])

        return "".join(result)
