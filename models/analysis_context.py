# -*- coding: utf-8 -*-
"""
Analysis context data models used for the AI 分析助手面板.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AnalysisTargetColumn:
    """Target sheet column entry rendered in the Analysis tab."""

    key: str
    display_name: str
    checked: bool = True
    disabled: bool = False
    tooltip: Optional[str] = None


@dataclass
class AnalysisSourceColumn:
    """Source sheet column entry rendered under a sheet group."""

    key: str
    display_name: str
    checked: bool = True
    tooltip: Optional[str] = None


@dataclass
class AnalysisSourceSheet:
    """Represents a collapsible sheet within the Analysis tab."""

    sheet_name: str
    display_name: str
    columns: List[AnalysisSourceColumn] = field(default_factory=list)
    expanded: bool = False


@dataclass
class AnalysisPanelState:
    """Aggregated state injected into the Analysis tab widget."""

    workbook_id: Optional[str] = None
    target_sheets: List[str] = field(default_factory=list)
    current_target_sheet: Optional[str] = None
    target_columns: List[AnalysisTargetColumn] = field(default_factory=list)
    source_sheets: List[AnalysisSourceSheet] = field(default_factory=list)
    has_workbook: bool = False
    placeholder_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.has_workbook or not self.target_sheets
