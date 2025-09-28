#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据索引管理工具
提供高效的数据搜索和索引功能
"""

from typing import Dict, List, Set, Any, Optional, Tuple, Union
import re
from collections import defaultdict
from datetime import datetime


class DataIndexer:
    """数据索引管理器"""

    def __init__(self):
        """初始化索引器"""
        # 各种索引
        self.name_index = defaultdict(list)  # 名称索引
        self.sheet_index = defaultdict(list)  # 工作表索引
        self.keyword_index = defaultdict(set)  # 关键词索引
        self.numeric_index = defaultdict(list)  # 数值索引
        self.level_index = defaultdict(list)  # 层级索引

        # 元数据
        self.indexed_items = {}  # 所有被索引的项目
        self.last_update = None

    def add_item(self, item_id: str, item_data: Dict[str, Any], item_type: str) -> None:
        """
        添加项目到索引

        Args:
            item_id: 项目唯一标识
            item_data: 项目数据
            item_type: 项目类型 ('target' 或 'source')
        """
        # 存储项目信息
        self.indexed_items[item_id] = {
            'data': item_data,
            'type': item_type,
            'indexed_at': datetime.now().isoformat()
        }

        # 构建各种索引
        self._build_name_index(item_id, item_data, item_type)
        self._build_sheet_index(item_id, item_data, item_type)
        self._build_keyword_index(item_id, item_data, item_type)

        if item_type == 'target':
            self._build_level_index(item_id, item_data)
        elif item_type == 'source':
            self._build_numeric_index(item_id, item_data)

        self.last_update = datetime.now()

    def _build_name_index(self, item_id: str, item_data: Dict[str, Any], item_type: str) -> None:
        """构建名称索引"""
        name = item_data.get('name', '').lower().strip()
        if name:
            self.name_index[name].append((item_type, item_id))

            # 同时索引原始文本（如果存在）
            if item_type == 'target' and 'original_text' in item_data:
                original = item_data['original_text'].lower().strip()
                if original and original != name:
                    self.name_index[original].append((item_type, item_id))

    def _build_sheet_index(self, item_id: str, item_data: Dict[str, Any], item_type: str) -> None:
        """构建工作表索引"""
        sheet_name = item_data.get('sheet_name', '')
        if sheet_name:
            self.sheet_index[sheet_name].append((item_type, item_id))

    def _build_keyword_index(self, item_id: str, item_data: Dict[str, Any], item_type: str) -> None:
        """构建关键词索引"""
        # 提取所有文本内容
        texts = []
        if 'name' in item_data:
            texts.append(item_data['name'])
        if item_type == 'target' and 'original_text' in item_data:
            texts.append(item_data['original_text'])

        # 从文本中提取关键词
        keywords = set()
        for text in texts:
            if text:
                # 提取中文词语
                chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
                keywords.update(chinese_words)

                # 提取英文单词
                english_words = re.findall(r'[a-zA-Z]+', text.lower())
                keywords.update(english_words)

                # 提取数字
                numbers = re.findall(r'\d+', text)
                keywords.update(numbers)

        # 建立关键词索引
        for keyword in keywords:
            if len(keyword) >= 2:  # 过滤太短的关键词
                self.keyword_index[keyword].add((item_type, item_id))

    def _build_level_index(self, item_id: str, item_data: Dict[str, Any]) -> None:
        """构建层级索引（仅目标项）"""
        level = item_data.get('level', 1)
        self.level_index[level].append(item_id)

    def _build_numeric_index(self, item_id: str, item_data: Dict[str, Any]) -> None:
        """构建数值索引（仅来源项）"""
        value = item_data.get('value')
        if isinstance(value, (int, float)):
            # 按数值范围建立索引
            if value == 0:
                range_key = '0'
            elif value > 0:
                if value < 1000:
                    range_key = '0-1k'
                elif value < 10000:
                    range_key = '1k-10k'
                elif value < 100000:
                    range_key = '10k-100k'
                elif value < 1000000:
                    range_key = '100k-1m'
                else:
                    range_key = '1m+'
            else:
                range_key = 'negative'

            self.numeric_index[range_key].append(item_id)

    def search_by_name(self, name: str, exact_match: bool = False) -> List[Tuple[str, str]]:
        """
        根据名称搜索

        Args:
            name: 搜索名称
            exact_match: 是否精确匹配

        Returns:
            List[Tuple[str, str]]: (item_type, item_id) 列表
        """
        name_lower = name.lower().strip()

        if exact_match:
            return self.name_index.get(name_lower, [])
        else:
            results = []
            for indexed_name, items in self.name_index.items():
                if name_lower in indexed_name or indexed_name in name_lower:
                    results.extend(items)
            return results

    def search_by_keywords(self, keywords: Union[str, List[str]]) -> List[Tuple[str, str]]:
        """
        根据关键词搜索

        Args:
            keywords: 关键词或关键词列表

        Returns:
            List[Tuple[str, str]]: (item_type, item_id) 列表
        """
        if isinstance(keywords, str):
            keywords = [keywords]

        all_results = set()

        for keyword in keywords:
            keyword_lower = keyword.lower().strip()

            # 精确匹配
            if keyword_lower in self.keyword_index:
                all_results.update(self.keyword_index[keyword_lower])

            # 模糊匹配
            for indexed_keyword, items in self.keyword_index.items():
                if keyword_lower in indexed_keyword or indexed_keyword in keyword_lower:
                    all_results.update(items)

        return list(all_results)

    def search_by_sheet(self, sheet_name: str) -> List[Tuple[str, str]]:
        """根据工作表名称搜索"""
        return self.sheet_index.get(sheet_name, [])

    def search_by_level(self, level: int) -> List[str]:
        """根据层级搜索目标项"""
        return self.level_index.get(level, [])

    def search_by_value_range(self, min_value: Optional[float] = None,
                             max_value: Optional[float] = None) -> List[str]:
        """
        根据数值范围搜索来源项

        Args:
            min_value: 最小值
            max_value: 最大值

        Returns:
            List[str]: item_id 列表
        """
        results = []

        for item_id in self.get_items_by_type('source'):
            item_data = self.indexed_items[item_id]['data']
            value = item_data.get('value')

            if isinstance(value, (int, float)):
                if min_value is not None and value < min_value:
                    continue
                if max_value is not None and value > max_value:
                    continue
                results.append(item_id)

        return results

    def fuzzy_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        模糊搜索

        Args:
            query: 查询字符串
            limit: 结果限制

        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        query_lower = query.lower().strip()
        results = []

        # 搜索名称
        name_results = self.search_by_name(query, exact_match=False)
        for item_type, item_id in name_results:
            item_data = self.indexed_items[item_id]['data']
            score = self._calculate_relevance_score(query_lower, item_data)
            results.append({
                'item_id': item_id,
                'item_type': item_type,
                'item_data': item_data,
                'score': score,
                'match_type': 'name'
            })

        # 搜索关键词
        keyword_results = self.search_by_keywords(query)
        for item_type, item_id in keyword_results:
            if item_id not in [r['item_id'] for r in results]:  # 避免重复
                item_data = self.indexed_items[item_id]['data']
                score = self._calculate_relevance_score(query_lower, item_data)
                results.append({
                    'item_id': item_id,
                    'item_type': item_type,
                    'item_data': item_data,
                    'score': score,
                    'match_type': 'keyword'
                })

        # 按相关性评分排序
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:limit]

    def _calculate_relevance_score(self, query: str, item_data: Dict[str, Any]) -> float:
        """计算相关性评分"""
        score = 0.0

        # 名称匹配评分
        name = item_data.get('name', '').lower()
        if query in name:
            score += 10.0
            if name.startswith(query):
                score += 5.0
            if name == query:
                score += 10.0

        # 原始文本匹配评分（如果存在）
        if 'original_text' in item_data:
            original = item_data['original_text'].lower()
            if query in original:
                score += 5.0

        # 长度匹配评分
        if name:
            length_ratio = len(query) / len(name)
            if 0.3 <= length_ratio <= 1.0:
                score += length_ratio * 3.0

        return score

    def get_items_by_type(self, item_type: str) -> List[str]:
        """获取指定类型的所有项目ID"""
        return [item_id for item_id, info in self.indexed_items.items()
                if info['type'] == item_type]

    def get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取项目数据"""
        if item_id in self.indexed_items:
            return self.indexed_items[item_id]['data']
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        target_count = len(self.get_items_by_type('target'))
        source_count = len(self.get_items_by_type('source'))

        return {
            'total_items': len(self.indexed_items),
            'target_items': target_count,
            'source_items': source_count,
            'name_index_entries': len(self.name_index),
            'sheet_index_entries': len(self.sheet_index),
            'keyword_index_entries': len(self.keyword_index),
            'level_index_entries': len(self.level_index),
            'numeric_index_entries': len(self.numeric_index),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

    def clear_index(self) -> None:
        """清空所有索引"""
        self.name_index.clear()
        self.sheet_index.clear()
        self.keyword_index.clear()
        self.numeric_index.clear()
        self.level_index.clear()
        self.indexed_items.clear()
        self.last_update = None

    def rebuild_index(self, items: Dict[str, Any]) -> None:
        """重建索引"""
        self.clear_index()

        for item_id, item_info in items.items():
            self.add_item(item_id, item_info['data'], item_info['type'])

    def export_index(self) -> Dict[str, Any]:
        """导出索引数据"""
        return {
            'indexed_items': self.indexed_items,
            'statistics': self.get_statistics(),
            'export_time': datetime.now().isoformat()
        }

    def suggest_similar_items(self, item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """建议相似项目"""
        if item_id not in self.indexed_items:
            return []

        item_info = self.indexed_items[item_id]
        item_data = item_info['data']
        item_name = item_data.get('name', '')

        # 基于名称相似性查找
        similar_results = []

        for other_id, other_info in self.indexed_items.items():
            if other_id == item_id:
                continue

            other_data = other_info['data']
            other_name = other_data.get('name', '')

            # 计算相似性
            similarity = self._calculate_similarity(item_name, other_name)

            if similarity > 0.3:  # 相似性阈值
                similar_results.append({
                    'item_id': other_id,
                    'item_type': other_info['type'],
                    'item_data': other_data,
                    'similarity': similarity
                })

        # 按相似性排序
        similar_results.sort(key=lambda x: x['similarity'], reverse=True)

        return similar_results[:limit]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似性"""
        if not text1 or not text2:
            return 0.0

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # 简单的相似性算法
        common_chars = sum(1 for c in text1_lower if c in text2_lower)
        max_length = max(len(text1), len(text2))

        if max_length == 0:
            return 0.0

        return common_chars / max_length