"""Configuration helpers for CHEVEL AI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ChevelConfig:
    """Runtime configuration with conservative local defaults."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    memory_db_path: Path = PROJECT_ROOT / "data" / "memory" / "chevel.db"
    memory_json_dir: Path = PROJECT_ROOT / "data" / "memory" / "interactions"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("CHEVEL_MODEL", "llama3.1:8b")
    public_model_name: str = os.getenv("CHEVEL_PUBLIC_MODEL", "HELI 1.5")
    max_history: int = int(os.getenv("CHEVEL_MAX_HISTORY", "20"))
    allowed_programs: Dict[str, List[str]] = field(default_factory=lambda: {
        "calculadora": ["calc.exe"],
        "calc": ["calc.exe"],
        "bloco de notas": ["notepad.exe"],
        "notepad": ["notepad.exe"],
        "explorador": ["explorer.exe"],
        "explorer": ["explorer.exe"],
    })
    search_roots: List[Path] = field(default_factory=lambda: [
        PROJECT_ROOT,
        Path(r"C:\END0-SYM\chevel"),
        Path.home(),
    ])


def get_config() -> ChevelConfig:
    """Return the process-wide configuration."""
    return ChevelConfig()


def resolve_model_name(model_name: str | None) -> str:
    """Resolve the public model name to the temporary local backend model."""
    config = get_config()
    requested = (model_name or config.public_model_name).strip()
    if requested.lower() == config.public_model_name.lower():
        return config.ollama_model
    return requested or config.ollama_model


def public_model_name(model_name: str | None = None) -> str:
    """Return the user-facing model name for UI/API responses."""
    config = get_config()
    requested = (model_name or "").strip()
    normalized = requested.lower()
    if not requested or requested == config.ollama_model or normalized.startswith("llama"):
        return config.public_model_name
    return requested
