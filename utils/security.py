"""Security guardrails for local actions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from utils.config_manager import get_config
from utils.native_bridge import allowed_program_command, known_programs


class SecurityError(ValueError):
    """Raised when a requested action is outside the MVP safety policy."""


SHELL_META_RE = re.compile(r"[;&|<>`]")


@dataclass(frozen=True)
class ServoLimit:
    """Physical safety limits for one servo channel."""

    name: str
    min_angle: float
    max_angle: float
    home_angle: float


DEFAULT_SERVO_LIMITS: List[ServoLimit] = [
    ServoLimit("base", 0.0, 180.0, 90.0),
    ServoLimit("shoulder", 15.0, 165.0, 90.0),
    ServoLimit("elbow", 10.0, 170.0, 90.0),
    ServoLimit("wrist", 0.0, 180.0, 90.0),
    ServoLimit("gripper", 20.0, 160.0, 90.0),
]


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


def validate_servo_angles(
    angles: Sequence[float],
    limits: Sequence[ServoLimit] | None = None,
) -> List[float]:
    """Validate servo angles against physical limits before motor output."""
    selected_limits = list(limits or DEFAULT_SERVO_LIMITS)
    if len(angles) != len(selected_limits):
        raise SecurityError(
            f"Esperados {len(selected_limits)} angulos de servo, recebidos {len(angles)}."
        )

    validated: List[float] = []
    for raw_angle, limit in zip(angles, selected_limits):
        try:
            angle = float(raw_angle)
        except (TypeError, ValueError) as exc:
            raise SecurityError(f"Angulo invalido para {limit.name}: {raw_angle}") from exc
        if angle < limit.min_angle or angle > limit.max_angle:
            raise SecurityError(
                f"Angulo fora do limite fisico em {limit.name}: "
                f"{angle:.1f} fora de {limit.min_angle:.1f}-{limit.max_angle:.1f}"
            )
        validated.append(round(angle, 2))
    return validated


def validate_cartesian_workspace(
    x: float,
    y: float,
    z: float,
    min_radius: float = 25.0,
    max_radius: float = 260.0,
    min_z: float = -40.0,
    max_z: float = 220.0,
) -> None:
    """Validate that a cartesian target is inside the simulated arm workspace."""
    radius = (float(x) ** 2 + float(y) ** 2) ** 0.5
    if radius < min_radius or radius > max_radius:
        raise SecurityError(
            f"Alvo fora do alcance radial seguro: {radius:.1f}mm "
            f"fora de {min_radius:.1f}-{max_radius:.1f}mm."
        )
    if float(z) < min_z or float(z) > max_z:
        raise SecurityError(
            f"Alvo fora do alcance vertical seguro: {float(z):.1f}mm "
            f"fora de {min_z:.1f}-{max_z:.1f}mm."
        )
