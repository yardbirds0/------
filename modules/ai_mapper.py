#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Mapping Service Module
Integrate with OpenAI API for intelligent mapping suggestions
"""

import sys
import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    WorkbookManager, TargetItem, SourceItem, MappingFormula,
    FormulaStatus
)


class AIMapper:
    """AI Mapping Service Class"""

    def __init__(self):
        """Initialize AI Mapper"""
        self.config = {}  # Use simple dict instead of AIConfiguration
        self.last_request_time = None
        self.request_count = 0

        # Default system prompt based on requirements
        self.default_system_prompt = """You are an experienced CPA (Certified Public Accountant) who is proficient in Chinese Accounting Standards (CAS). Your task is to analyze financial statement items and establish mathematical mapping relationships between them.

I will provide you with a JSON object containing two key parts:
1. `target_items`: A list of financial statement items that need to be calculated and filled, including their names and hierarchical relationships.
2. `source_items`: All available data sources from different data sheets (such as income statement, balance sheet), including their sheet names, item names, and cell positions.

Your task is:
1. Carefully analyze each `target_item`.
2. Based on your professional accounting knowledge, find one or more related items from the `source_items` list to construct a mathematical formula for calculating the `target_item` value.
3. Formulas can only use `+`, `-`, `*`, `/` operators.
4. **Output format must strictly follow JSON specifications**. Return a list named "mappings", where each object contains "target_id" and corresponding "formula" string.
5. **Formula string format must be: `[SheetName]![ItemName]`**. For example: `[Income Statement]![Operating Cost] + [Income Statement]![Taxes and Surcharges]`.
6. If a `target_item` cannot find any mapping relationship from `source_items`, do not create a mapping entry for it.
7. Pay special attention to the hierarchical relationships of `target_items` and keywords in names such as "minus:", "including:", "plus:", etc., which indicate calculation logic.

Please think like a rigorous accountant and ensure the accuracy of the formulas."""

    def configure_service(self, config: Dict[str, Any]) -> bool:
        """Configure AI service parameters"""
        try:
            self.config.update_config(**config)
            if not self.config.system_prompt:
                self.config.system_prompt = self.default_system_prompt

            print(f"AI service configured: {self.config.model_name}")
            return True
        except Exception as e:
            print(f"Configuration failed: {str(e)}")
            return False

    def test_connection(self) -> Tuple[bool, str]:
        """Test AI service connection"""
        if not self.config.is_valid():
            return False, "Invalid configuration"

        try:
            test_payload = {
                "model": self.config.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a connection test."}
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }

            response = requests.post(
                self.config.api_endpoint,
                headers=headers,
                json=test_payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def build_mapping_request(self, target_items: List[TargetItem],
                             source_items: List[SourceItem]) -> Dict[str, Any]:
        """Build structured AI mapping request"""

        # Build target items data
        target_data = []
        for item in target_items:
            target_data.append({
                "id": item.id,
                "name": item.name,
                "level": item.level,
                "parent_id": item.parent_id,
                "is_empty": item.is_empty_target
            })

        # Build source items data
        source_data = []
        for item in source_items:
            source_data.append({
                "id": item.id,
                "sheet": item.sheet_name,
                "name": item.name,
                "cell": item.cell_address,
                "value": item.value
            })

        # Build request payload
        request_data = {
            "task_description": "Please generate mapping formulas for each target item based on provided target and source items. Follow accounting standards for matching.",
            "target_items": target_data,
            "source_items": source_data
        }

        return request_data

    def call_ai_service(self, request_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Call AI service for mapping suggestions"""

        if not self.config.is_valid():
            return False, {"error": "Invalid AI configuration"}

        try:
            # Build OpenAI API request
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": json.dumps(request_data, ensure_ascii=False, indent=2)}
            ]

            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }

            print(f"Calling AI service: {self.config.model_name}")
            print(f"Target items: {len(request_data['target_items'])}")
            print(f"Source items: {len(request_data['source_items'])}")

            # Make API request
            response = requests.post(
                self.config.api_endpoint,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            self.last_request_time = datetime.now()
            self.request_count += 1

            if response.status_code == 200:
                result = response.json()
                return True, result
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(error_msg)
                return False, {"error": error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            print(error_msg)
            return False, {"error": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(error_msg)
            return False, {"error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return False, {"error": error_msg}

    def parse_ai_response(self, response: Dict[str, Any]) -> List[MappingFormula]:
        """Parse AI response to mapping formulas"""
        mapping_formulas = []

        try:
            # Extract content from OpenAI response
            if "choices" not in response or not response["choices"]:
                print("No choices in AI response")
                return mapping_formulas

            content = response["choices"][0].get("message", {}).get("content", "")

            if not content:
                print("No content in AI response")
                return mapping_formulas

            print(f"AI Response Content: {content[:200]}...")

            # Try to parse JSON from content
            try:
                # Sometimes AI wraps JSON in code blocks
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    if end > start:
                        content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    if end > start:
                        content = content[start:end].strip()

                mapping_data = json.loads(content)

            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {str(e)}")
                print(f"Content: {content}")
                return mapping_formulas

            # Extract mappings
            if "mappings" not in mapping_data:
                print("No 'mappings' key in parsed data")
                return mapping_formulas

            mappings = mapping_data["mappings"]
            print(f"Found {len(mappings)} mappings in AI response")

            # Create MappingFormula objects
            for mapping in mappings:
                if "target_id" not in mapping or "formula" not in mapping:
                    continue

                target_id = mapping["target_id"]
                formula = mapping["formula"]

                # Validate formula format
                if self._validate_formula_format(formula):
                    mapping_formula = MappingFormula(
                        target_id=target_id,
                        formula=formula,
                        status=FormulaStatus.AI_GENERATED,
                        created_by="ai"
                    )

                    # Set as valid initially (will be validated later)
                    mapping_formula.set_validation_result(True)

                    mapping_formulas.append(mapping_formula)
                else:
                    print(f"Invalid formula format: {formula}")

        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")

        print(f"Successfully parsed {len(mapping_formulas)} mapping formulas")
        return mapping_formulas

    def _validate_formula_format(self, formula: str) -> bool:
        """Validate formula format"""
        if not formula or not formula.strip():
            return False

        # Check for basic formula elements
        import re

        # Should contain at least one reference in [Sheet]![Item] format
        references = re.findall(r'\[([^\]]+)\]!\[([^\]]+)\]', formula)

        if not references:
            return False

        # Check for valid operators
        valid_chars = set("[]!+-*/()0123456789. abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        # Add Chinese characters (simplified check)
        valid_chars.update(set("一二三四五六七八九十"))

        for char in formula:
            if ord(char) >= 0x4e00 and ord(char) <= 0x9fff:  # Chinese characters
                continue
            if char not in valid_chars:
                return False

        return True

    def generate_mappings(self, workbook_manager: WorkbookManager,
                         max_targets: int = 50) -> Tuple[bool, List[MappingFormula]]:
        """Generate mapping suggestions for all targets"""

        try:
            # Get all target and source items
            all_targets = list(workbook_manager.target_items.values())
            all_sources = list(workbook_manager.source_items.values())

            # Limit targets to avoid overwhelming the AI
            if len(all_targets) > max_targets:
                # Prioritize empty targets
                empty_targets = [t for t in all_targets if t.is_empty_target]
                if len(empty_targets) <= max_targets:
                    selected_targets = empty_targets
                else:
                    selected_targets = empty_targets[:max_targets]
            else:
                selected_targets = all_targets

            print(f"Processing {len(selected_targets)} target items")
            print(f"Available source items: {len(all_sources)}")

            # Build request
            request_data = self.build_mapping_request(selected_targets, all_sources)

            # Call AI service
            success, response = self.call_ai_service(request_data)

            if not success:
                return False, []

            # Parse response
            mapping_formulas = self.parse_ai_response(response)

            return True, mapping_formulas

        except Exception as e:
            print(f"Error generating mappings: {str(e)}")
            return False, []

    def get_service_stats(self) -> Dict[str, Any]:
        """Get AI service statistics"""
        return {
            "configured": self.config.is_valid(),
            "model_name": self.config.model_name,
            "api_endpoint": self.config.api_endpoint,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "request_count": self.request_count
        }


class AIConfigurationUI:
    """AI Configuration User Interface"""

    def __init__(self, parent=None, ai_mapper: AIMapper = None):
        """Initialize AI configuration UI"""
        self.parent = parent
        self.ai_mapper = ai_mapper or AIMapper()
        self.window = None

        # UI components
        self.endpoint_var = tk.StringVar(value=self.ai_mapper.config.api_endpoint)
        self.model_var = tk.StringVar(value=self.ai_mapper.config.model_name)
        self.api_key_var = tk.StringVar(value=self.ai_mapper.config.api_key)
        self.temperature_var = tk.DoubleVar(value=self.ai_mapper.config.temperature)
        self.max_tokens_var = tk.IntVar(value=self.ai_mapper.config.max_tokens)
        self.timeout_var = tk.IntVar(value=self.ai_mapper.config.timeout)

    def create_ui(self) -> tk.Toplevel:
        """Create AI configuration interface"""
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("AI Service Configuration")
        self.window.geometry("600x500")

        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # API Endpoint
        ttk.Label(main_frame, text="API Endpoint:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.endpoint_var, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Model Name
        ttk.Label(main_frame, text="Model Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, width=47)
        model_combo['values'] = ('gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k')
        model_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # API Key
        ttk.Label(main_frame, text="API Key:").grid(row=row, column=0, sticky=tk.W, pady=5)
        api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show="*", width=50)
        api_key_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Temperature
        ttk.Label(main_frame, text="Temperature:").grid(row=row, column=0, sticky=tk.W, pady=5)
        temp_frame = ttk.Frame(main_frame)
        temp_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Scale(temp_frame, from_=0.0, to=1.0, variable=self.temperature_var, orient=tk.HORIZONTAL).pack(fill=tk.X, side=tk.LEFT, expand=True)
        ttk.Label(temp_frame, textvariable=self.temperature_var, width=10).pack(side=tk.RIGHT)
        row += 1

        # Max Tokens
        ttk.Label(main_frame, text="Max Tokens:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=100, to=4000, textvariable=self.max_tokens_var, width=48).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Timeout
        ttk.Label(main_frame, text="Timeout (seconds):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=10, to=120, textvariable=self.timeout_var, width=48).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # System Prompt
        ttk.Label(main_frame, text="System Prompt:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=row, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(0, weight=1)

        self.prompt_text = tk.Text(prompt_frame, height=8, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical")
        prompt_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.prompt_text.config(yscrollcommand=prompt_scrollbar.set)
        prompt_scrollbar.config(command=self.prompt_text.yview)

        # Set default prompt
        self.prompt_text.insert(tk.END, self.ai_mapper.default_system_prompt)

        row += 1
        main_frame.rowconfigure(row-1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Test Connection", command=self._test_connection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save Configuration", command=self._save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Load Defaults", command=self._load_defaults).pack(side=tk.LEFT, padx=(0, 5))

        return self.window

    def _test_connection(self):
        """Test AI service connection"""
        # Save current config first
        self._save_config()

        success, message = self.ai_mapper.test_connection()

        if success:
            messagebox.showinfo("Test Result", f"Success: {message}")
        else:
            messagebox.showerror("Test Result", f"Failed: {message}")

    def _save_config(self):
        """Save AI configuration"""
        try:
            config = {
                'api_endpoint': self.endpoint_var.get(),
                'model_name': self.model_var.get(),
                'api_key': self.api_key_var.get(),
                'temperature': self.temperature_var.get(),
                'max_tokens': self.max_tokens_var.get(),
                'timeout': self.timeout_var.get(),
                'system_prompt': self.prompt_text.get(1.0, tk.END).strip()
            }

            success = self.ai_mapper.configure_service(config)

            if success:
                messagebox.showinfo("Configuration", "Settings saved successfully")
            else:
                messagebox.showerror("Configuration", "Failed to save settings")

        except Exception as e:
            messagebox.showerror("Configuration", f"Error: {str(e)}")

    def _load_defaults(self):
        """Load default configuration"""
        self.endpoint_var.set("https://api.openai.com/v1/chat/completions")
        self.model_var.set("gpt-4-turbo")
        self.api_key_var.set("")
        self.temperature_var.set(0.1)
        self.max_tokens_var.set(2000)
        self.timeout_var.set(30)
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, self.ai_mapper.default_system_prompt)


def main():
    """Main function for testing AI mapping module"""
    print("AI Mapping Service Test")
    print("="*50)

    # Create AI mapper
    ai_mapper = AIMapper()

    # Test configuration
    test_config = {
        'api_endpoint': 'https://api.openai.com/v1/chat/completions',
        'model_name': 'gpt-4-turbo',
        'api_key': 'test-key',  # Use your real API key for actual testing
        'temperature': 0.1,
        'max_tokens': 1000,
        'timeout': 30
    }

    success = ai_mapper.configure_service(test_config)
    print(f"Configuration: {'Success' if success else 'Failed'}")

    # Test connection (will fail with test key)
    # success, message = ai_mapper.test_connection()
    # print(f"Connection test: {message}")

    # Show service stats
    stats = ai_mapper.get_service_stats()
    print(f"\nService stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "="*50)
    print("Test completed")


if __name__ == "__main__":
    main()