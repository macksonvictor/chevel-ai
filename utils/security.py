"""Security guardrails for local actions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from utils.config_manager import get_config
from utils.native_bridge import allowed_program_command, known_programs


class SecurityError(ValueError):
    """Raised when a requested action is outside the MVP safety policy."""


SHELL_META_RE = re.compile(r"[;&|<>`]")


def clean_text(value: str) -> str:
    """Normalize user text before using it as a local action parameter."""
    return " ".join((value or "").strip().split())


def resolve_user_path(value: str, base: Path | None = None) -> Path:
    """Resolve a user path safely relative to the project root."""
    text = clean_text(value).strip('"').strip("'")
    if not text or "\x00" in text:
        raise SecurityError("Caminho vazio ou invalido.")

    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = (base or get_config().project_root) / candidate
    return candidate.expanduser().resolve()


def ensure_existing_path(value: str, base: Path | None = None) -> Path:
    """Return an existing resolved path or raise a clear error."""
    path = resolve_user_path(value, base)
    if not path.exists():
        raise SecurityError(f"Caminho nao encontrado: {path}")
    return path


def get_allowed_program_command(program_name: str) -> List[str]:
    """Resolve a program alias to an allowed command list."""
    normalized = clean_text(program_name).lower()
    if not normalized:
        raise SecurityError("Programa vazio.")
    if SHELL_META_RE.search(normalized):
        raise SecurityError("Comandos de shell nao sao permitidos no MVP.")

    try:
        native_command = allowed_program_command(normalized)
    except Exception as exc:
        raise SecurityError(str(exc)) from exc
    if native_command:
        return native_command

    allowed = get_config().allowed_programs
    command = allowed.get(normalized)
    if not command:
        native_known = known_programs()
        known = ", ".join(sorted(native_known or allowed))
        raise SecurityError(
            f"Programa nao permitido no MVP: {program_name}. Permitidos: {known}"
        )
    return list(command)


def safe_search_roots(roots: Iterable[Path] | None = None) -> List[Path]:
    """Return existing search roots without duplicates."""
    selected = roots or get_config().search_roots
    seen = set()
    result: List[Path] = []
    for root in selected:
        try:
            resolved = Path(root).expanduser().resolve()
        except OSError:
            continue
        if resolved.exists() and resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result
