"""
Prompts package for Email Productivity Agent

This package contains:
- Default prompt templates for core email processing functions
- Custom prompt templates for user-specific workflows
- Prompt management and versioning
"""

import json
import os
from typing import Dict, Any

def load_default_prompts() -> Dict[str, Any]:
    """Load default prompt templates"""
    prompts_file = os.path.join(os.path.dirname(__file__), 'default_prompts.json')
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading default prompts: {e}")
        return {}

def load_custom_prompts() -> Dict[str, Any]:
    """Load custom prompt templates"""
    prompts_file = os.path.join(os.path.dirname(__file__), 'custom_prompts.json')
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading custom prompts: {e}")
        return {}

def get_all_prompts() -> Dict[str, Any]:
    """Get all available prompts (default + custom)"""
    default_prompts = load_default_prompts()
    custom_prompts = load_custom_prompts()
    
    # Merge with custom prompts taking precedence
    all_prompts = default_prompts.copy()
    all_prompts.update(custom_prompts)
    
    return all_prompts

__all__ = ['load_default_prompts', 'load_custom_prompts', 'get_all_prompts']
__version__ = "1.0.0"
__description__ = "Prompt templates for Email Productivity Agent AI operations"