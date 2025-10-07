# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Purpose: AI-assisted financial report data mapping and filling tool (PySide6). It extracts data from Excel workbooks, generates/validates formulas, and fills “flash report” sheets (快报表).
- Tech stack: Python 3.x, PySide6 GUI, pytest for tests. Local assets under assets/, extensive UI and integration tests under tests/.

Quickstart (Windows, PowerShell)
- Create venv and install deps
  - python -m venv .venv
  - .\.venv\Scripts\activate
  - pip install -r requirements_pyside6.txt
- Run app
  - python main.py
- Run tests (pytest)
  - Run all: python -m pytest
  - Verbose: python -m pytest -v
  - Single file: python -m pytest tests\test_ui_integration.py
  - Single test: python -m pytest tests\test_ui_integration.py::TestClass::test_case
  - By keyword: python -m pytest -k "title_bar"
- Useful debug scripts (run directly)
  - python tests\debug_full_workflow.py  # end-to-end diagnosis from Excel load to compute
  - python tests\verify_gui_display.py   # verify source-tree/dropdowns
  - python tests\simple_test.py          # quick data model/rules check
  - python tests\list_sheet_names.py     # inspect Excel workbook sheet names

Notes
- No explicit lint/format config detected (e.g., ruff/flake8/black). Skip lint steps unless you add them.
- Many tests open UI windows (PySide6). Prefer targeted runs (single file/test) when iterating.
- File encoding convention: UTF-8 without BOM (project standard).

High-level architecture
- Entry point and UI shell
  - main.py builds a QMainWindow-based desktop app with dockable panels (QDockWidget), status bars, toolbars, and PySide6 widgets.
- Core domain/model layer (models/)
  - data_models.py defines core entities (e.g., TargetItem, SourceItem, MappingFormula, WorkbookManager, SheetType, MappingTemplate), statuses, and template management used across the app.
- Excel I/O and processing (modules/)
  - file_manager.py: workbook/file I/O and multi-workbook management.
  - data_extractor.py: parses Excel sheets, identifies target items (to be filled), source items, and hierarchy by indentation.
  - calculation_engine.py: evaluates formulas (+, -, *, /, parentheses) and computes values.
  - ai_mapper.py: uses LLMs to propose/initialize mapping formulas between targets and sources.
  - table_schema_analyzer.py, data_structure_processor.py: support schema/structure analysis.
- AI integration (modules/ai_integration/)
  - api_providers/: provider abstraction (e.g., OpenAI-compatible), base_provider.py for config, openai_provider.py, etc.
  - registry.py, chat_manager.py, streaming_handler.py: orchestration and streaming token handling for chat/LLM.
- Desktop UI components (components/ and widgets/)
  - components/advanced_widgets.py: custom widgets including the formula editor, syntax highlighter, tree/table helpers.
  - components/sheet_explorer.py and dialogs/sheet_classification_dialog.py: sheet navigation and classification flow.
  - components/chat/: self-contained chat UI (controllers, dialogs, services, renderers, widgets, styles) that integrates LLM features (model browser, prompt editor, request preview, API test service, token usage indicator, etc.).
  - widgets/: additional dialogs and panels for workbook classification and AI configuration.
- Persistence and data
  - data/chat/db_manager.py: local storage for chat-related data.
  - assets/icons/categories/ and assets/icons/providers/: icon lookup for model categories/providers (see their README.md files for naming rules).

Core data flow
1) File loading: FileManager opens one or more Excel workbooks.
2) Sheet classification: sheets are auto-tagged as Flash Reports (快报表) or Data Sources (keywords + user override).
3) Data extraction: DataExtractor builds structured targets/sources and hierarchy.
4) AI mapping: AIMapper proposes mapping formulas between targets and sources via LLM.
5) Calculation: CalculationEngine evaluates formulas and computes final values.
6) Export/write-back: results written to the appropriate sheets/cells.

Formulas
- Reference style: [SheetName]![ItemName] or [SheetName]CellAddress
  - Example: [利润表]![营业成本] + [利润表]![税金及附加]
  - Supported operators: +, -, *, /, (), with validation/highlighting in the editor.

Configuration touchpoints
- LLM integration expects a provider config (API URL/key/model). Tests reference config/ai_models.json; ensure it exists and aligns with providers in modules/ai_integration/.
- Icons for model categories/providers are resolved from assets/icons/... per the README rules.

Test suite overview (practical navigation)
- tests/ contains a large number of UI/integration/acceptance tests. Common patterns:
  - End-to-end/UI flows: test_ui_integration.py, test_end_to_end_integration.py, acceptance/ ...
  - Chat/AI: tests/chat/, test_openai_service.py, test_full_chat_flow.py
  - Excel analysis and validation: analyze_*.py, debug_*.py, verify_*.py scripts
- Prefer running specific files or -k filters during development to avoid launching many UI windows at once.

Project-specific rules distilled from CLAUDE.md and repo docs
- Keep source files in UTF-8 (no BOM).
- App targets Windows and PySide6; many tests are visual/interactive.
- LLM providers are abstracted; configure via provider configs (e.g., config/ai_models.json) and ensure assets/icons are available for a clean UI.
