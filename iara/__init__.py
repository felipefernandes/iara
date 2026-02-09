"""Iara - Revisora de Codigo com IA"""

__version__ = "1.0.0"

from iara.config import load_config, DEFAULT_CONFIG
from iara.prompt import generate_system_prompt
from iara.reviewer import review_code, review_code_with_model
from iara.scanner import scan_directory
