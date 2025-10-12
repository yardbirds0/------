# -*- coding: utf-8 -*-
"""
Controller responsible for managing the Analysis tab state and payload generation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Set

from models import (
    AnalysisPanelState,
    AnalysisSourceColumn,
    AnalysisSourceSheet,
    AnalysisTargetColumn,
    TargetItem,
    WorkbookManager,
)

logger = logging.getLogger(__name__)

ANALYSIS_PLACEHOLDER = "暂无表格分析请求"


@dataclass
class _ColumnMeta:
    key: str
    display_name: str
    is_data_column: bool


class AnalysisSessionController:
    """Tracks workbook-linked selections and generates analysis payloads."""

    def __init__(self, cache_dir: Path | str) -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._workbook: Optional[WorkbookManager] = None
        self._workbook_id: Optional[str] = None
        self._current_sheet: Optional[str] = None

        self._target_selection: Dict[str, Set[str]] = {}
        self._source_selection: Dict[str, Set[str]] = {}

        self._target_meta_by_key: Dict[str, Dict[str, _ColumnMeta]] = {}
        self._target_key_by_display: Dict[str, Dict[str, str]] = {}
        self._source_meta_by_key: Dict[str, Dict[str, _ColumnMeta]] = {}
        self._source_key_by_display: Dict[str, Dict[str, str]] = {}

        self._target_parent_lookup: Dict[str, str] = {}
        self._target_identifier_lookup: Dict[str, Optional[str]] = {}
        self._target_lookup: Dict[str, TargetItem] = {}
        self._source_parent_lookup: Dict[str, Dict[str, str]] = {}
        self._source_items_by_sheet: Dict[str, List] = {}

        self._panel_state: AnalysisPanelState = AnalysisPanelState()
        self._last_payload: Optional[Dict[str, object]] = None
        self._latest_warnings: List[str] = []

        self._state_callback: Optional[Callable[[AnalysisPanelState], None]] = None
        self._payload_callback: Optional[Callable[[Dict[str, object]], None]] = None

    @staticmethod
    def _normalize_display_name(name: Optional[str]) -> str:
        if not name:
            return ""
        cleaned = re.sub(r"\s*\(\d+\)$", "", str(name)).strip()
        if cleaned:
            return cleaned
        return str(name).strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_callbacks(
        self,
        *,
        on_state_change: Optional[Callable[[AnalysisPanelState], None]] = None,
        on_payload_change: Optional[Callable[[Dict[str, object]], None]] = None,
    ) -> None:
        self._state_callback = on_state_change
        self._payload_callback = on_payload_change

    def sync_context(
        self,
        workbook: Optional[WorkbookManager],
        *,
        current_sheet: Optional[str] = None,
        target_column_config: Optional[List[Dict[str, object]]] = None,
        source_column_configs: Optional[Dict[str, List[Dict[str, object]]]] = None,
    ) -> AnalysisPanelState:
        """Synchronises selections and metadata with the latest workbook state."""

        if workbook is None or not workbook.flash_report_sheets:
            logger.debug("No workbook loaded, resetting analysis state.")
            self._reset_context()
            self._emit_state()
            return self._panel_state

        workbook_id = self._derive_workbook_id(workbook)
        if workbook_id != self._workbook_id:
            logger.debug("Detected new workbook context: %s", workbook_id)
            self._load_persisted_selection(workbook_id)

        self._workbook = workbook
        self._workbook_id = workbook_id

        self._build_metadata_maps()
        self._current_sheet = self._resolve_current_sheet(
            requested=current_sheet, available=workbook.flash_report_sheets
        )

        self._ensure_target_selection(target_column_config)
        self._ensure_source_selection(source_column_configs or {})

        self._update_panel_state()
        self._persist_selection()
        self._emit_state()
        return self._panel_state

    def handle_target_sheet_change(self, sheet_name: str) -> None:
        if not sheet_name or sheet_name == self._current_sheet:
            return
        if not self._workbook or sheet_name not in (self._workbook.flash_report_sheets or []):
            return
        logger.debug("Switching analysis target sheet to %s", sheet_name)
        self._current_sheet = sheet_name
        self._last_payload = None
        self._update_panel_state()
        self._emit_state()

    def handle_target_column_toggle(self, column_key: str, checked: bool) -> None:
        if not self._current_sheet and self._panel_state.current_target_sheet:
            self._current_sheet = self._panel_state.current_target_sheet
        if not self._current_sheet:
            logger.warning("Target sheet is undefined; ignoring column toggle for %s", column_key)
            return
        selection = self._target_selection.setdefault(self._current_sheet, set())
        if checked:
            selection.add(column_key)
        else:
            selection.discard(column_key)
        logger.debug(
            "Target column %s toggled to %s for sheet %s",
            column_key,
            checked,
            self._current_sheet,
        )
        self._last_payload = None
        self._persist_selection()
        self._update_panel_state()
        self._emit_state()

    def handle_source_column_toggle(
        self,
        sheet_name: str,
        column_key: str,
        checked: bool,
    ) -> None:
        if not sheet_name:
            return
        selection = self._source_selection.setdefault(sheet_name, set())
        if checked:
            selection.add(column_key)
        else:
            selection.discard(column_key)
        logger.debug(
            "Source column %s toggled to %s for sheet %s",
            column_key,
            checked,
            sheet_name,
        )
        self._last_payload = None
        self._persist_selection()
        self._update_panel_state()
        self._emit_state()

    def build_payload(self) -> Optional[Dict[str, object]]:
        if not self._workbook or not self._current_sheet:
            logger.warning("Cannot build payload without workbook or current sheet.")
            return None

        selected_targets = self._target_selection.get(self._current_sheet, set())
        if not selected_targets:
            logger.debug("No target columns selected, payload will not be built.")
            return None

        self._latest_warnings = []

        payload: Dict[str, object] = {
            "global_context": self._build_global_context(),
            "current_target_sheet": self._build_target_sheet_info(
                self._current_sheet, selected_targets
            ),
            "targets_to_map": self._build_targets_to_map(
                self._current_sheet, selected_targets
            ),
            "source_sheets": self._build_source_payload(),
        }

        self._last_payload = payload
        if hasattr(self._panel_state, "warnings"):
            self._panel_state.warnings = list(self._latest_warnings)
        if self._payload_callback:
            try:
                self._payload_callback(payload)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to dispatch payload callback: %s", exc)
        return payload

    def _build_global_context(self) -> Dict[str, object]:
        now = datetime.now()
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "reporting_period": now.strftime("%Y-%m"),
            "currency": "CNY",
            "accounting_standard": "CAS (中国企业会计准则)",
        }

    def get_latest_warnings(self) -> List[str]:
        return list(self._latest_warnings)

    def get_panel_state(self) -> AnalysisPanelState:
        return self._panel_state

    def get_cached_payload(self) -> Optional[Dict[str, object]]:
        return self._last_payload

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _reset_context(self) -> None:
        self._workbook = None
        self._workbook_id = None
        self._current_sheet = None
        self._target_selection.clear()
        self._source_selection.clear()
        self._target_meta_by_key.clear()
        self._source_meta_by_key.clear()
        self._panel_state = AnalysisPanelState()
        self._last_payload = None
        self._latest_warnings = []

    def _derive_workbook_id(self, workbook: WorkbookManager) -> str:
        file_path = getattr(workbook, "file_path", "") or ""
        base_name = Path(file_path).stem if file_path else (workbook.file_name or "workbook")
        digest_source = file_path or workbook.file_name or "workbook"
        digest = hashlib.sha1(digest_source.encode("utf-8", "ignore")).hexdigest()[:10]
        return f"{base_name}_{digest}"

    def _cache_file(self, workbook_id: str) -> Path:
        safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in workbook_id)
        return self._cache_dir / f"{safe_id}.json"

    def _load_persisted_selection(self, workbook_id: str) -> None:
        cache_file = self._cache_file(workbook_id)
        if not cache_file.exists():
            self._target_selection.clear()
            self._source_selection.clear()
            return

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            self._target_selection = {
                sheet: set(columns or []) for sheet, columns in data.get("target_selection", {}).items()
            }
            self._source_selection = {
                sheet: set(columns or []) for sheet, columns in data.get("source_selection", {}).items()
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load analysis selection cache: %s", exc)
            self._target_selection.clear()
            self._source_selection.clear()

    def _persist_selection(self) -> None:
        if not self._workbook_id:
            return
        cache_file = self._cache_file(self._workbook_id)
        data = {
            "target_selection": {sheet: sorted(columns) for sheet, columns in self._target_selection.items()},
            "source_selection": {sheet: sorted(columns) for sheet, columns in self._source_selection.items()},
        }
        try:
            cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to persist analysis selection: %s", exc)

    def _resolve_current_sheet(
        self, *, requested: Optional[str], available: Iterable[str]
    ) -> Optional[str]:
        available_list = list(available or [])
        if not available_list:
            return None
        if requested and requested in available_list:
            return requested
        if self._current_sheet and self._current_sheet in available_list:
            return self._current_sheet
        return available_list[0]

    def _build_metadata_maps(self) -> None:
        assert self._workbook is not None

        self._target_meta_by_key.clear()
        self._target_key_by_display.clear()
        self._source_meta_by_key.clear()
        self._source_key_by_display.clear()

        for sheet, entries in (self._workbook.target_sheet_columns or {}).items():
            meta_map: Dict[str, _ColumnMeta] = {}
            display_map: Dict[str, str] = {}
            for entry in entries or []:
                key = str(entry.get("key") or entry.get("display_name") or entry.get("column_letter"))
                display_name_raw = str(entry.get("display_name") or key)
                display_name = str(
                    entry.get("normalized_display")
                    or self._normalize_display_name(display_name_raw)
                    or display_name_raw
                )
                meta = _ColumnMeta(
                    key=key,
                    display_name=display_name,
                    is_data_column=bool(entry.get("is_data_column", True)),
                )
                meta_map[key] = meta
                display_map[display_name] = key
                if display_name != display_name_raw and display_name_raw not in display_map:
                    display_map[display_name_raw] = key
            self._target_meta_by_key[sheet] = meta_map
            self._target_key_by_display[sheet] = display_map

        for sheet, entries in (self._workbook.source_sheet_columns or {}).items():
            meta_map: Dict[str, _ColumnMeta] = {}
            display_map: Dict[str, str] = {}
            for entry in entries or []:
                key = str(entry.get("key") or entry.get("display_name") or entry.get("column_letter"))
                display_name_raw = str(entry.get("display_name") or key)
                display_name = str(
                    entry.get("normalized_display")
                    or self._normalize_display_name(display_name_raw)
                    or display_name_raw
                )
                meta = _ColumnMeta(
                    key=key,
                    display_name=display_name,
                    is_data_column=bool(entry.get("is_data_column", True)),
                )
                meta_map[key] = meta
                display_map[display_name] = key
                if display_name != display_name_raw and display_name_raw not in display_map:
                    display_map[display_name_raw] = key
            self._source_meta_by_key[sheet] = meta_map
            self._source_key_by_display[sheet] = display_map

        self._build_parent_lookups()

    def _build_parent_lookups(self) -> None:
        assert self._workbook is not None
        self._target_lookup = {
            item.id: item for item in self._workbook.target_items.values()
        }
        self._target_parent_lookup = {
            item_id: item.name for item_id, item in self._target_lookup.items()
        }
        self._target_identifier_lookup = {
            item_id: (item.identifier or None)
            for item_id, item in self._target_lookup.items()
        }

        self._source_parent_lookup = {}
        self._source_items_by_sheet = {}
        for item in self._workbook.source_items.values():
            sheet_map = self._source_parent_lookup.setdefault(item.sheet_name, {})
            if item.account_code:
                sheet_map[item.account_code] = item.parent_code or ""
            self._source_items_by_sheet.setdefault(item.sheet_name, []).append(item)

    def _ensure_target_selection(self, column_config: Optional[List[Dict[str, object]]]) -> None:
        if not self._current_sheet:
            return

        meta = self._target_meta_by_key.get(self._current_sheet, {})
        display_map = self._target_key_by_display.get(self._current_sheet, {})
        available_keys = set(meta.keys())

        persisted = self._target_selection.get(self._current_sheet, set())
        normalised_persisted = {display_map.get(key, key) for key in persisted}
        valid_persisted = {key for key in normalised_persisted if key in available_keys}

        default_enabled: Set[str] = set()
        if column_config:
            default_enabled = {
                display_map.get(str(entry.get("name")), str(entry.get("name")))
                for entry in column_config
                if entry.get("enabled", True)
            }
        else:
            default_enabled = {key for key, info in meta.items() if info.is_data_column}

        if not valid_persisted:
            valid_persisted = {key for key in default_enabled if key in available_keys}

        if not valid_persisted and available_keys:
            valid_persisted = set(list(available_keys)[:3])

        self._target_selection[self._current_sheet] = valid_persisted

    def _ensure_source_selection(self, column_configs: Dict[str, List[Dict[str, object]]]) -> None:
        for sheet, meta in self._source_meta_by_key.items():
            display_map = self._source_key_by_display.get(sheet, {})
            available_keys = set(meta.keys())

            persisted = self._source_selection.get(sheet, set())
            normalised = {display_map.get(key, key) for key in persisted}
            valid_persisted = {key for key in normalised if key in available_keys}

            config_entries = column_configs.get(sheet, []) or []
            if config_entries:
                defaults = {
                    display_map.get(str(entry.get("name")), str(entry.get("name")))
                    for entry in config_entries
                    if entry.get("enabled", True)
                }
            else:
                defaults = {key for key, info in meta.items() if info.is_data_column}

            if not valid_persisted:
                valid_persisted = {key for key in defaults if key in available_keys}

            if not valid_persisted and available_keys:
                valid_persisted = set(list(available_keys)[:5])

            self._source_selection[sheet] = valid_persisted

    def _update_panel_state(self) -> None:
        has_workbook = bool(self._workbook and self._workbook.flash_report_sheets)
        if not has_workbook:
            self._panel_state = AnalysisPanelState()
            return

        target_columns: List[AnalysisTargetColumn] = []
        if self._current_sheet:
            meta = self._target_meta_by_key.get(self._current_sheet, {})
            selected = self._target_selection.get(self._current_sheet, set())
            for column in meta.values():
                target_columns.append(
                    AnalysisTargetColumn(
                        key=column.key,
                        display_name=column.display_name,
                        checked=column.key in selected,
                    )
                )

        source_sheets: List[AnalysisSourceSheet] = []
        for sheet, meta in self._source_meta_by_key.items():
            selected = self._source_selection.get(sheet, set())
            columns = [
                AnalysisSourceColumn(
                    key=column.key,
                    display_name=column.display_name,
                    checked=column.key in selected,
                )
                for column in meta.values()
            ]
            source_sheets.append(
                AnalysisSourceSheet(
                    sheet_name=sheet,
                    display_name=sheet,
                    columns=columns,
                    expanded=False,
                )
            )

        self._panel_state = AnalysisPanelState(
            workbook_id=self._workbook_id,
            target_sheets=list(self._workbook.flash_report_sheets or []),
            current_target_sheet=self._current_sheet,
            target_columns=target_columns,
            source_sheets=source_sheets,
            has_workbook=has_workbook,
            placeholder_reason=None if has_workbook else "未加载工作簿",
            warnings=list(self._latest_warnings),
        )

    def _emit_state(self) -> None:
        if self._state_callback:
            try:
                self._state_callback(self._panel_state)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to dispatch analysis state: %s", exc)

    def _build_target_sheet_info(
        self, sheet_name: str, selected_columns: Set[str]
    ) -> Dict[str, object]:
        meta_values = list(self._target_meta_by_key.get(sheet_name, {}).values())
        available_columns = [meta.display_name for meta in meta_values]

        columns_to_map: List[str] = []
        if selected_columns:
            for meta in meta_values:
                if meta.key in selected_columns:
                    columns_to_map.append(meta.display_name)

        info: Dict[str, object] = {
            "name": sheet_name,
            "available_columns": available_columns,
        }
        if columns_to_map:
            info["columns_to_map"] = columns_to_map
        return info

    def _build_targets_to_map(
        self,
        sheet_name: str,
        selected_columns: Set[str],
    ) -> Dict[str, Dict[str, object]]:
        assert self._workbook is not None
        result: Dict[str, Dict[str, object]] = {}

        for target in self._workbook.target_items.values():
            if target.sheet_name != sheet_name:
                continue

            identifier = target.identifier
            if identifier is None:
                self._record_warning(
                    "目标项 '%s' (工作表: %s) 缺少层级编号，已在请求中以 null 表示。",
                    target.name,
                    sheet_name,
                )

            parent_identifier = target.resolve_parent_identifier(self._target_lookup)
            if target.parent_id and parent_identifier is None:
                self._record_warning(
                    "目标项 '%s' (工作表: %s) 的父级缺少层级编号，parent_identifier 将输出 null。",
                    target.name,
                    sheet_name,
                )

            result[target.name] = {
                "identifier": identifier,
                "parent_identifier": parent_identifier,
            }

        return result

    def _build_source_payload(self) -> Dict[str, Dict[str, object]]:
        assert self._workbook is not None
        payload: Dict[str, Dict[str, object]] = {}

        for sheet, selected_columns in self._source_selection.items():
            if not selected_columns:
                continue
            meta_lookup = self._source_meta_by_key.get(sheet, {})
            items = []
            for item in self._source_items_by_sheet.get(sheet, []):
                column_values: Dict[str, object] = {}
                for column_key in selected_columns:
                    meta = meta_lookup.get(column_key)
                    display_name = meta.display_name if meta else column_key
                    if display_name not in column_values:
                        column_values[display_name] = ""

                    value = None
                    if column_key in item.data_columns:
                        value = item.data_columns[column_key]
                    elif display_name in item.data_columns:
                        value = item.data_columns[display_name]

                    if value is not None and value != "":
                        column_values[display_name] = value

                if not column_values:
                    continue

                parent_identifier = item.parent_identifier
                if parent_identifier is None and getattr(item, "parent_hierarchical_number", ""):
                    parent_identifier = item.parent_hierarchical_number or None

                identifier = item.identifier
                if identifier is None:
                    self._record_warning(
                        "来源项 '%s' (工作表: %s) 缺少唯一标识符，已在请求中以 null 表示。",
                        item.name,
                        sheet,
                    )

                item_payload = {
                    "name": item.name,
                    "identifier": identifier,
                    "parent_identifier": parent_identifier,
                    "columns": column_values,
                }

                items.append(item_payload)

            if items:
                payload[sheet] = {"items": items}

        return payload

    def _record_warning(self, message: str, *args: object) -> None:
        if args:
            formatted = message % args
        else:
            formatted = message
        logger.warning(formatted)
        self._latest_warnings.append(formatted)

    # ------------------------------------------------------------------
    # Public helpers for integration
    # ------------------------------------------------------------------
    def get_current_sheet_name(self) -> Optional[str]:
        return self._current_sheet

    def get_selected_target_columns(self) -> Set[str]:
        if not self._current_sheet:
            return set()
        return set(self._target_selection.get(self._current_sheet, set()))

    def resolve_target_column_key(self, display_name: str) -> Optional[str]:
        if not self._current_sheet:
            return None
        key = self._target_key_by_display.get(self._current_sheet, {}).get(display_name)
        if key:
            return key
        if display_name in self._target_meta_by_key.get(self._current_sheet, {}):
            return display_name
        return None
