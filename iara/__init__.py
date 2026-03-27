"""Iara - AI Code Reviewer"""

__version__ = "1.10.0"

from iara.config import load_config, DEFAULT_CONFIG
from iara.prompt import generate_system_prompt
from iara.reviewer import review_code, review_code_with_model
from iara.scanner import scan_directory
from iara.auth import resolve_api_key, validate_api_key
