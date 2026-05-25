"""Fast reflex loop for CHEVEL safety rules."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional

from utils.native_bridge import evaluate_reflexes


class Gatilho(str, Enum):
    SENSOR_VALOR = "sensor_valor"
    TIMEOUT = "timeout"


@dataclass
class RegraReflexa:
    nome: str
    descricao: str
    prioridade: int
    gatilho: Gatilho
    condicao: Callable[[Dict], bool]
    acao: Callable[[Dict], Dict] | None = None
    cooldown: float = 1.0
    ultimo_disparo: float = 0.0

    def avaliar(self, estado: Dict) -> Optional[Dict]:
        now = time.time()
        if now - self.ultimo_disparo < self.cooldown:
            return None
        if not self.condicao(estado):
            return None
        self.ultimo_disparo = now
        payload = self.acao(estado) if self.acao else {}
        return {
            "nome": self.nome,
            "descricao": self.descricao,
            "prioridade": self.prioridade,
            "acao": payload or {"tipo": "reflexo", "nome": self.nome},
        }


class FastThinkingSystem:
    """Millisecond reflex checks without LLM involvement."""

    def __init__(self, reflex_callback: Callable[[Dict], None] | None = None):
        self.estado_sensores: Dict = {}
        self.regras: List[RegraReflexa] = []
        self.frequencia_hz = 100
        self.ultimo_tick = 0.0
        self.tick_count = 0
        self.emergency_active = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self.ultimos_reflexos: List[Dict] = []
        self._callbacks: List[Callable[[Dict], None]] = []
        self._last_reflex_by_name: Dict[str, float] = {}
        if reflex_callback:
            self._callbacks.append(reflex_callback)
        self._registrar_regras_padrao()

    def iniciar_loop(self, frequencia_hz: int = 100) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.frequencia_hz = max(1, frequencia_hz)
        self._stop.clear()
        interval = 1.0 / self.frequencia_hz
        self._thread = threading.Thread(target=self._loop, args=(interval,), daemon=True)
        self._thread.start()

    def parar_loop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def atualizar_sensores(self, dados: Dict) -> List[Dict]:
        with self._lock:
            self.estado_sensores.update(dados)
            return self.avaliar_reflexos()

    def registrar_regra(self, regra: RegraReflexa) -> None:
        with self._lock:
            self.regras.append(regra)
            self.regras.sort(key=lambda item: item.prioridade, reverse=True)

    def registrar_callback(self, callback: Callable[[Dict], None]) -> None:
        """Register a callback called when a reflex fires."""
        with self._lock:
            self._callbacks.append(callback)

    def limpar_estado_emergencia(self) -> None:
        """Clear the emergency flag after a human safety check."""
        with self._lock:
            self.emergency_active = False

    def avaliar_reflexos(self) -> List[Dict]:
        native = evaluate_reflexes(self.estado_sensores)
        if native:
            return self._record_reflexes(native)

        reflexos = []
        for regra in self.regras:
            result = regra.avaliar(self.estado_sensores)
            if result:
                reflexos.append(result)
        return self._record_reflexes(reflexos)

    def estado(self) -> Dict:
        return {
            "sensores": dict(self.estado_sensores),
            "regras": len(self.regras),
            "loop_ativo": bool(self._thread and self._thread.is_alive()),
            "frequencia_hz": self.frequencia_hz,
            "ultimo_tick": self.ultimo_tick,
            "tick_count": self.tick_count,
            "emergency_active": self.emergency_active,
            "ultimos_reflexos": list(self.ultimos_reflexos),
        }

    def _loop(self, interval: float) -> None:
        while not self._stop.is_set():
            started = time.perf_counter()
            with self._lock:
                self.ultimo_tick = time.time()
                self.tick_count += 1
                self.avaliar_reflexos()
            elapsed = time.perf_counter() - started
            time.sleep(max(0.0, interval - elapsed))

    def _record_reflexes(self, reflexes: List[Dict]) -> List[Dict]:
        filtered = self._filter_cooldown(reflexes)
        if not filtered:
            return []
        for reflex in filtered:
            action = reflex.get("acao", {})
            if action.get("tipo") == "parada_emergencia":
                self.emergency_active = True
            for callback in list(self._callbacks):
                try:
                    callback(reflex)
                except Exception:
                    continue
        self.ultimos_reflexos = (self.ultimos_reflexos + filtered)[-10:]
        return filtered

    def _filter_cooldown(self, reflexes: List[Dict]) -> List[Dict]:
        now = time.time()
        selected: List[Dict] = []
        for reflex in sorted(reflexes, key=lambda item: int(item.get("prioridade", 0)), reverse=True):
            name = str(reflex.get("nome", "reflexo"))
            priority = int(reflex.get("prioridade", 0))
            cooldown = 0.1 if priority >= 90 else 1.0
            if now - self._last_reflex_by_name.get(name, 0.0) < cooldown:
                continue
            self._last_reflex_by_name[name] = now
            selected.append(reflex)
        return selected

    def _registrar_regras_padrao(self) -> None:
        self.registrar_regra(RegraReflexa(
            nome="pessoa_zona_braco",
            descricao="Pessoa detectada na zona do braco -> parada emergencia",
            prioridade=100,
            gatilho=Gatilho.SENSOR_VALOR,
            condicao=lambda estado: bool(estado.get("pessoa_detectada_zona_braco")),
            acao=lambda estado: {"tipo": "parada_emergencia", "motivo": "pessoa_zona_braco"},
            cooldown=0.5,
        ))
        self.registrar_regra(RegraReflexa(
            nome="temp_motor_alta",
            descricao="Temperatura do motor acima de 80C -> desligar motor",
            prioridade=95,
            gatilho=Gatilho.SENSOR_VALOR,
            condicao=lambda estado: float(estado.get("temp_motor_max", 0) or 0) > 80,
            acao=lambda estado: {"tipo": "desligar_motor", "motivo": "temperatura"},
        ))
        self.registrar_regra(RegraReflexa(
            nome="bateria_baixa",
            descricao="Bateria abaixo de 10% -> parada emergencia",
            prioridade=90,
            gatilho=Gatilho.SENSOR_VALOR,
            condicao=lambda estado: float(estado.get("bateria", 100) or 100) < 10,
            acao=lambda estado: {"tipo": "parada_emergencia", "motivo": "bateria_baixa"},
        ))
        self.registrar_regra(RegraReflexa(
            nome="sobrecorrente_motor",
            descricao="Sobrecorrente acima de 4A -> reduzir potencia",
            prioridade=85,
            gatilho=Gatilho.SENSOR_VALOR,
            condicao=lambda estado: float(estado.get("corrente_motor_max", 0) or 0) > 4,
            acao=lambda estado: {"tipo": "reduzir_potencia", "motivo": "sobrecorrente"},
        ))
        self.registrar_regra(RegraReflexa(
            nome="heartbeat_perdido",
            descricao="Sem heartbeat por mais de 5s -> ir para home",
            prioridade=80,
            gatilho=Gatilho.TIMEOUT,
            condicao=lambda estado: bool(estado.get("ultimo_heartbeat")) and time.time() - float(estado.get("ultimo_heartbeat")) > 5,
            acao=lambda estado: {"tipo": "ir_para_home", "motivo": "heartbeat_perdido"},
        ))
        self.registrar_regra(RegraReflexa(
            nome="pressao_garra_baixa",
            descricao="Pressao da garra abaixo de 30% -> apertar garra",
            prioridade=75,
            gatilho=Gatilho.SENSOR_VALOR,
            condicao=lambda estado: "pressao_garra" in estado and float(estado.get("pressao_garra") or 0) < 0.3,
            acao=lambda estado: {"tipo": "apertar_garra", "motivo": "pressao_baixa"},
        ))


fast_thinking = FastThinkingSystem()
