"""Optional bridge to the CHEVEL C++ native module."""

from __future__ import annotations

import json
import math
import subprocess
import time
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
        return _assess_action_risk_fallback(action, parameters or {})
    return result


def evaluate_reflexes(sensor_state: Dict) -> List[Dict]:
    """Ask the C++ quick core to evaluate reflex rules when available."""
    payload = json.dumps(sensor_state or {}, ensure_ascii=False)
    if _native is not None and hasattr(_native, "evaluate_reflexes"):
        return _normalize_critical_reflexes(
            [dict(item) for item in _native.evaluate_reflexes(sensor_state or {})],
            sensor_state or {},
        )

    result = _call_service(["reflex", payload])
    if not result or not result.get("ok"):
        return _evaluate_reflexes_fallback(sensor_state or {})
    reflexes = result.get("reflexes", [])
    if not isinstance(reflexes, list):
        return _evaluate_reflexes_fallback(sensor_state or {})
    return _normalize_critical_reflexes([dict(item) for item in reflexes], sensor_state or {})


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


def _assess_action_risk_fallback(action: str, parameters: Dict) -> Dict:
    key = str(action or "").strip().lower()
    risk = "medio"
    requires_confirmation = True
    reason = "acao desconhecida"

    if key == "buscar_arquivo":
        risk = "seguro"
        requires_confirmation = False
        reason = "busca local limitada"
    elif key in {"abrir_arquivo", "controlar_luz"}:
        risk = "baixo"
        requires_confirmation = False
        reason = "acao local reversivel ou stub"
    elif key == "executar_programa":
        serialized = json.dumps(parameters or {}, ensure_ascii=False)
        if any(token in serialized for token in ["&", "|", ";", "<", ">", "`"]):
            risk = "critico"
            reason = "metacaracter de shell detectado"
        else:
            risk = "baixo"
            requires_confirmation = False
            reason = "programa ainda sera validado por allowlist"
    elif key in {"dume_emergency_stop"}:
        risk = "seguro"
        requires_confirmation = False
        reason = "parada segura simulada"
    elif key == "dume_command":
        command = str(parameters.get("command", "")).strip().lower()
        if command in {"status", "capabilities", "diagnostics", "emergency_stop", "stop"}:
            risk = "seguro"
            requires_confirmation = False
            reason = "comando robotico informativo ou parada segura"
        elif command in {"home", "open_gripper"}:
            risk = "medio"
            requires_confirmation = False
            reason = "comando robotico reversivel em simulacao"
        else:
            risk = "alto"
            reason = "comando robotico fisico exige confirmacao no MVP"
    elif key in {"enviar_email", "mover_braco"}:
        risk = "alto"
        reason = "acao externa ou fisica requer confirmacao no MVP"

    return {
        "ok": True,
        "risk": risk,
        "requires_confirmation": requires_confirmation,
        "reason": reason,
        "engine": "python-fallback",
    }


def _evaluate_reflexes_fallback(sensor_state: Dict) -> List[Dict]:
    reflexes: List[Dict] = []

    def add(nome: str, descricao: str, prioridade: int, tipo: str, motivo: str) -> None:
        reflexes.append({
            "nome": nome,
            "descricao": descricao,
            "prioridade": prioridade,
            "acao": {"tipo": tipo, "motivo": motivo},
            "engine": "python-fallback",
        })

    if bool(sensor_state.get("pessoa_detectada_zona_braco")):
        add("pessoa_zona_braco", "Pessoa detectada na zona do braco", 100, "parada_emergencia", "pessoa_zona_braco")
    if float(sensor_state.get("temp_motor_max", 0) or 0) > 80:
        add("temp_motor_alta", "Temperatura do motor acima de 80C", 95, "desligar_motor", "temperatura")
    if float(sensor_state.get("bateria", 100) or 100) < 10:
        add("bateria_baixa", "Bateria abaixo de 10%", 90, "parada_emergencia", "bateria_baixa")
    if float(sensor_state.get("corrente_motor_max", 0) or 0) > 4:
        add("sobrecorrente_motor", "Sobrecorrente acima de 4A", 85, "reduzir_potencia", "sobrecorrente")
    if sensor_state.get("ultimo_heartbeat") and time.time() - float(sensor_state.get("ultimo_heartbeat")) > 5:
        add("heartbeat_perdido", "Sem heartbeat por mais de 5s", 80, "ir_para_home", "heartbeat_perdido")
    if "pressao_garra" in sensor_state and float(sensor_state.get("pressao_garra") or 0) < 0.3:
        add("pressao_garra_baixa", "Pressao da garra abaixo de 30%", 75, "apertar_garra", "pressao_baixa")

    return reflexes


def _normalize_critical_reflexes(reflexes: List[Dict], sensor_state: Dict) -> List[Dict]:
    """Keep old native binaries aligned with current critical safety policy."""
    if float(sensor_state.get("bateria", 100) or 100) < 10:
        upgraded = False
        for item in reflexes:
            if item.get("nome") == "bateria_baixa":
                item["acao"] = {"tipo": "parada_emergencia", "motivo": "bateria_baixa"}
                upgraded = True
        if not upgraded:
            reflexes.append({
                "nome": "bateria_baixa",
                "descricao": "Bateria abaixo de 10%",
                "prioridade": 90,
                "acao": {"tipo": "parada_emergencia", "motivo": "bateria_baixa"},
                "engine": "python-safety-normalizer",
            })
    return reflexes
