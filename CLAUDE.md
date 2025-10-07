# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-assisted financial report data mapping and filling tool (AI辅助财务报表数据映射与填充工具) built with PySide6. The application automates the process of extracting data from multiple "source data sheets" in Excel workbooks, performing calculations (addition, subtraction, multiplication, division), and filling the results into "flash report sheets" (快报表).

## Commands

### Running the Application
```bash
python main.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/verify_fixes.py

# Run with verbose output
pytest -v
```

### Installing Dependencies
```bash
pip install -r requirements_pyside6.txt
```

## High-Level Architecture

### Core Data Flow
1. **File Loading**: Excel workbooks are loaded through `FileManager` which manages multiple workbooks simultaneously
2. **Sheet Classification**: Sheets are automatically classified as either "Flash Reports" (快报表) or "Data Source Sheets" based on keywords, with user override capability
3. **Data Extraction**: `DataExtractor` parses sheets to identify:
   - Target items (empty cells in flash reports that need filling)
   - Source items (data values from source sheets)
   - Hierarchical relationships based on indentation
4. **AI Mapping**: `AIMapper` uses LLM to generate initial mapping formulas between source and target items
5. **Calculation**: `CalculationEngine` evaluates formulas and computes values
6. **Export**: Results are written back to Excel files

### Key Modules

- **models/data_models.py**: Core data structures including `TargetItem`, `SourceItem`, `MappingFormula`, `WorkbookManager`
- **modules/file_manager.py**: Handles Excel file I/O and workbook management
- **modules/data_extractor.py**: Extracts structured data from Excel sheets
- **modules/ai_mapper.py**: Integrates with LLMs for intelligent formula generation
- **modules/calculation_engine.py**: Formula parsing and calculation engine
- **components/advanced_widgets.py**: Custom PySide6 widgets including formula editor with syntax highlighting
- **components/sheet_explorer.py**: Sheet navigation and classification UI

### UI Structure

The application uses a four-panel layout:
1. **Left Panel**: Sheet explorer and target item structure tree
2. **Central Panel**: Main workbench with mapping formula editor
3. **Right Panel**: Source item library, formula inspector, property inspector
4. **Bottom Panel**: Output logs and system messages

### Formula Format

Formulas use the format: `[SheetName]![ItemName]` or `[SheetName]CellAddress`
- Example: `[利润表]![营业成本] + [利润表]![税金及附加]`
- Supports operators: `+`, `-`, `*`, `/`, `(`, `)`

### Important Conventions

- **Encoding**: All files must use UTF-8 encoding without BOM
- **Sheet Detection**: Sheets containing "快报" are auto-classified as flash reports
- **Hierarchy Detection**: Item hierarchy is determined by leading spaces/indentation in column B
- **Target Cell Format**: Assumes column A has index, column B has item name, column D has values
- **Progress Tracking**: Progress is tracked in `progress.md` at root level

### Testing Approach

The project includes various test and debug scripts in the `tests/` directory:
- `verify_fixes.py`: Validates data display and extraction
- `analyze_excel_headers.py`: Analyzes Excel header structures
- `debug_full_workflow.py`: Tests complete data processing pipeline

### AI Integration

The application integrates with OpenAI-compatible LLMs. Configuration includes:
- API URL/Endpoint
- API Key
- Model Name (e.g., gpt-4-turbo, claude-3-opus)
- System Prompt (customizable for financial domain expertise)

### Development Notes

- The application is designed for 1920x1080+ displays
- Uses QDockWidget for flexible, customizable panel layouts
- Implements drag-and-drop mapping from source items to formulas
- Provides real-time formula syntax highlighting and validation
- Supports template saving/loading for reusable mapping configurations


