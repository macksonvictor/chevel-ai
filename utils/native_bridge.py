"""Optional bridge to the CHEVEL C++ native module."""

from __future__ import annotations

import math
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from utils.config_manager import PROJECT_ROOT


try:
    import chevel_native as _native
except Exception:  # pragma: no cover - depends on local compiler state
    _native = None


_SERVICE_PATH = PROJECT_ROOT / "native" / "bin" / "chevel_core.exe"


def native_available() -> bool:
    """Return True when the C++ extension is importable."""
    return _native is not None or _SERVICE_PATH.exists()


def native_version() -> str:
    """Return the native module version or a fallback marker."""
    if _native is None:
        service = _call_service(["version"])
        if service and service.get("ok"):
            return str(service.get("version"))
        return "python-fallback"
    return _native.version()


def cosine_similarity_batch(
    query: Sequence[float], vectors: Iterable[Sequence[float]]
) -> List[float]:
    """Calculate cosine similarity, using C++ when available."""
    query_list = [float(item) for item in query]
    vector_list = [[float(item) for item in vector] for vector in vectors]

    if _native is not None:
        return list(_native.cosine_similarity_batch(query_list, vector_list))
    return [_cosine_similarity(query_list, vector) for vector in vector_list]


def detect_intent(message: str) -> Optional[Dict]:
    """Detect an action through the C++ core when available."""
    if _native is not None:
        result = dict(_native.detect_intent(message))
    else:
        result = _call_service(["detect", message])
        if not result:
            return None
    if not result.get("matched"):
        return None
    return result


def allowed_program_command(program: str) -> Optional[List[str]]:
    """Validate a program name through the C++ core when available."""
    if _native is not None:
        return list(_native.allowed_program_command(program))

    result = _call_service(["program", program])
    if not result:
        return None
    if not result.get("ok"):
        raise ValueError(str(result.get("error", "Erro C++ desconhecido.")))
    return list(result.get("command", []))


def known_programs() -> Optional[List[str]]:
    """Return allowlisted programs from C++ when available."""
    if _native is None:
        return None
    return list(_native.known_programs())


def assess_action_risk(action: str, parameters: Optional[Dict] = None) -> Optional[Dict]:
    """Ask the C++ quick core to classify action risk when available."""
    payload = json.dumps(parameters or {}, ensure_ascii=False)
    if _native is not None and hasattr(_native, "assess_action_risk"):
        return dict(_native.assess_action_risk(action, parameters or {}))

    result = _call_service(["risk", action, payload])
    if not result or not result.get("ok"):
        return None
    return result


def evaluate_reflexes(sensor_state: Dict) -> Optional[List[Dict]]:
    """Ask the C++ quick core to evaluate reflex rules when available."""
    payload = json.dumps(sensor_state or {}, ensure_ascii=False)
    if _native is not None and hasattr(_native, "evaluate_reflexes"):
        return [dict(item) for item in _native.evaluate_reflexes(sensor_state or {})]

    result = _call_service(["reflex", payload])
    if not result or not result.get("ok"):
        return None
    reflexes = result.get("reflexes", [])
    if not isinstance(reflexes, list):
        return None
    return [dict(item) for item in reflexes]


def _call_service(args: Sequence[str]) -> Optional[Dict]:
    if not _SERVICE_PATH.exists():
        return None
    try:
        completed = subprocess.run(
            [str(_SERVICE_PATH), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if not completed.stdout.strip():
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same size.")
    dot = sum(left * right for left, right in zip(a, b))
    norm_a = math.sqrt(sum(item * item for item in a))
    norm_b = math.sqrt(sum(item * item for item in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
