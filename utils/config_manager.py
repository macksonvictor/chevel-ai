"""Configuration helpers for CHEVEL AI.

Runtime values come from three layers, in this order:

1. conservative code defaults;
2. optional ``data/configs/*.local.json`` files plus ``CHEVEL_CONFIG_PATH``;
3. environment variables.

The public repository ships only ``*.example.json`` files. Local ``*.local.json``
files are intentionally ignored so ports, paths, and private integration values
do not leak into Git.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "data" / "configs"
DEFAULT_ALLOWED_PROGRAMS = {
    "calculadora": ["calc.exe"],
    "calc": ["calc.exe"],
    "bloco de notas": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "explorador": ["explorer.exe"],
    "explorer": ["explorer.exe"],
}
DEFAULT_SEARCH_ROOTS = [
    PROJECT_ROOT,
    Path(r"C:\END0-SYM\chevel"),
    Path.home(),
]


@dataclass(frozen=True)
class ChevelConfig:
    """Runtime configuration with conservative local defaults."""

    project_root: Path = PROJECT_ROOT
    config_dir: Path = CONFIG_DIR
    data_dir: Path = PROJECT_ROOT / "data"
    memory_db_path: Path = PROJECT_ROOT / "data" / "memory" / "chevel.db"
    memory_json_dir: Path = PROJECT_ROOT / "data" / "memory" / "interactions"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("CHEVEL_MODEL", "llama3.1:8b")
    public_model_name: str = os.getenv("CHEVEL_PUBLIC_MODEL", "HELI 1.5")
    max_history: int = int(os.getenv("CHEVEL_MAX_HISTORY", "20"))
    allowed_programs: Dict[str, List[str]] = field(default_factory=lambda: dict(DEFAULT_ALLOWED_PROGRAMS))
    search_roots: List[Path] = field(default_factory=lambda: list(DEFAULT_SEARCH_ROOTS))
    voice_enabled: bool = False
    voice_backend: str = "browser"
    voice_language: str = "pt-BR"
    voice_wake_phrase: str = "ola chevel"
    dume_mode: str = "simulation"
    dume_hardware_connected: bool = False
    dume_require_confirmation: bool = True
    dume_telemetry_interval_sec: float = 0.25
    robot_arm_port: str | None = None
    robot_arm_baudrate: int = 115200
    robot_arm_simulate: bool = True
    safety_motion_requires_confirmation: bool = True
    safety_emergency_stop_enabled: bool = True
    integrations: Dict[str, Dict] = field(default_factory=dict)
    raw_config: Dict = field(default_factory=dict)


def get_config() -> ChevelConfig:
    """Return the process-wide configuration."""
    return load_config()


def load_config(
    *,
    config_dir: str | Path | None = None,
    config_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ChevelConfig:
    """Load CHEVEL runtime config from optional local JSON files.

    ``config_dir`` and ``env`` are exposed for tests; normal runtime should call
    ``get_config()``.
    """
    env_map = env if env is not None else os.environ
    root = PROJECT_ROOT
    resolved_config_dir = _resolve_path(config_dir or CONFIG_DIR, root)
    payload = _load_local_payload(
        resolved_config_dir,
        config_path or env_map.get("CHEVEL_CONFIG_PATH"),
    )

    data_dir = _resolve_path(_get_nested(payload, "paths", "data_dir", default="data"), root)
    memory_db_path = _resolve_path(
        _get_nested(payload, "paths", "memory_db_path", default=data_dir / "memory" / "chevel.db"),
        root,
    )
    memory_json_dir = _resolve_path(
        _get_nested(payload, "paths", "memory_json_dir", default=data_dir / "memory" / "interactions"),
        root,
    )
    search_roots = [
        _resolve_path(path, root)
        for path in _get_nested(payload, "paths", "search_roots", default=DEFAULT_SEARCH_ROOTS)
    ]

    return ChevelConfig(
        project_root=root,
        config_dir=resolved_config_dir,
        data_dir=data_dir,
        memory_db_path=memory_db_path,
        memory_json_dir=memory_json_dir,
        ollama_host=env_map.get(
            "OLLAMA_HOST",
            str(_get_nested(payload, "core", "ollama_host", default="http://127.0.0.1:11434")),
        ),
        ollama_model=env_map.get(
            "CHEVEL_MODEL",
            str(_get_nested(payload, "core", "ollama_model", default="llama3.1:8b")),
        ),
        public_model_name=env_map.get(
            "CHEVEL_PUBLIC_MODEL",
            str(_get_nested(payload, "core", "public_model_name", default="HELI 1.5")),
        ),
        max_history=int(env_map.get(
            "CHEVEL_MAX_HISTORY",
            _get_nested(payload, "core", "max_history", default=20),
        )),
        allowed_programs=_coerce_allowed_programs(
            _get_nested(payload, "actions", "allowed_programs", default=DEFAULT_ALLOWED_PROGRAMS)
        ),
        search_roots=search_roots,
        voice_enabled=_as_bool(_get_nested(payload, "voice", "enabled", default=False)),
        voice_backend=str(_get_nested(payload, "voice", "backend", default="browser")),
        voice_language=str(_get_nested(payload, "voice", "language", default="pt-BR")),
        voice_wake_phrase=str(_get_nested(payload, "voice", "wake_phrase", default="ola chevel")),
        dume_mode=str(_get_nested(payload, "dume", "mode", default="simulation")),
        dume_hardware_connected=_as_bool(_get_nested(payload, "dume", "hardware_connected", default=False)),
        dume_require_confirmation=_as_bool(_get_nested(payload, "dume", "require_confirmation", default=True)),
        dume_telemetry_interval_sec=float(_get_nested(payload, "dume", "telemetry_interval_sec", default=0.25)),
        robot_arm_port=_none_if_blank(_get_nested(payload, "robot_arm", "port", default=None)),
        robot_arm_baudrate=int(_get_nested(payload, "robot_arm", "baudrate", default=115200)),
        robot_arm_simulate=_as_bool(_get_nested(payload, "robot_arm", "simulate", default=True)),
        safety_motion_requires_confirmation=_as_bool(
            _get_nested(payload, "safety", "motion_requires_confirmation", default=True)
        ),
        safety_emergency_stop_enabled=_as_bool(
            _get_nested(payload, "safety", "emergency_stop_enabled", default=True)
        ),
        integrations=dict(payload.get("integrations", {})) if isinstance(payload.get("integrations", {}), dict) else {},
        raw_config=payload,
    )


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


def _load_local_payload(config_dir: Path, explicit_path: str | Path | None = None) -> Dict:
    payload: Dict = {}
    if config_dir.exists():
        for path in sorted(config_dir.glob("*.local.json")):
            _deep_merge(payload, _read_json(path))

    if explicit_path:
        explicit = _resolve_path(explicit_path, PROJECT_ROOT)
        _deep_merge(payload, _read_json(explicit))

    return payload


def _read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a JSON object: {path}")
    return data


def _deep_merge(base: MutableMapping, overlay: Mapping) -> MutableMapping:
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), MutableMapping):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _get_nested(payload: Mapping, *keys: str, default=None):
    current = payload
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def _resolve_path(value: str | Path, root: Path) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


def _coerce_allowed_programs(value) -> Dict[str, List[str]]:
    if not isinstance(value, Mapping):
        return dict(DEFAULT_ALLOWED_PROGRAMS)
    programs: Dict[str, List[str]] = {}
    for key, commands in value.items():
        if isinstance(commands, str):
            programs[str(key)] = [commands]
        elif isinstance(commands, Iterable):
            programs[str(key)] = [str(command) for command in commands]
    return programs or dict(DEFAULT_ALLOWED_PROGRAMS)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "sim", "on"}
    return bool(value)


def _none_if_blank(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
