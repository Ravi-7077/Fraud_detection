from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def _resolve_values(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {key: _resolve_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_values(item) for item in value]
    return value


def load_config(path: str | None = None) -> dict:
    config_path = Path(path or os.getenv("CONFIG_YAML") or DEFAULT_CONFIG_PATH)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    config = yaml.safe_load(config_path.read_text()) or {}
    return _resolve_values(config)
