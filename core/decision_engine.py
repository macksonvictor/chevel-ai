"""Autonomous decision engine for safe CHEVEL actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional

from utils.native_bridge import assess_action_risk


class NivelRisco(str, Enum):
    """Risk levels used before CHEVEL executes an action."""

    SEGURO = "seguro"
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass
class AcaoCandidata:
    """Candidate action scored by the decision engine."""

    acao: str
    parametros: Dict = field(default_factory=dict)
    prioridade: float = 0.5
    urgencia: float = 0.0
    custo_recurso: float = 0.0
    irreversivel: bool = False
    origem: str = "intent"

    @classmethod
    def from_dict(cls, payload: Dict) -> "AcaoCandidata":
        return cls(
            acao=str(payload.get("acao", "")),
            parametros=dict(payload.get("parametros", {})),
            prioridade=float(payload.get("prioridade", payload.get("confianca", 0.5))),
            urgencia=float(payload.get("urgencia", 0.0)),
            custo_recurso=float(payload.get("custo_recurso", 0.0)),
            irreversivel=bool(payload.get("irreversivel", False)),
            origem=str(payload.get("engine", payload.get("origem", "intent"))),
        )

    def to_action_dict(self) -> Dict:
        return {
            "tipo": "acao",
            "acao": self.acao,
            "parametros": self.parametros,
            "prioridade": self.prioridade,
            "urgencia": self.urgencia,
            "custo_recurso": self.custo_recurso,
            "irreversivel": self.irreversivel,
            "origem": self.origem,
        }


@dataclass
class Decisao:
    """Decision result for one or more candidate actions."""

    acao_escolhida: Optional[AcaoCandidata]
    score: float
    risco: NivelRisco
    requer_confirmacao: bool
    justificativa: str
    confianca: float

    def to_dict(self) -> Dict:
        return {
            "acao": self.acao_escolhida.to_action_dict() if self.acao_escolhida else None,
            "score": self.score,
            "risco": self.risco.value,
            "requer_confirmacao": self.requer_confirmacao,
            "justificativa": self.justificativa,
            "confianca": self.confianca,
        }


class DecisionEngine:
    """Choose the best action while enforcing MVP safety policy."""

    RISK_PENALTY = {
        NivelRisco.SEGURO: 0.0,
        NivelRisco.BAIXO: 0.1,
        NivelRisco.MEDIO: 0.35,
        NivelRisco.ALTO: 0.7,
        NivelRisco.CRITICO: 1.0,
    }

    def decidir(self, acoes_candidatas: Iterable[Dict | AcaoCandidata], estado_mundo: Dict | None = None) -> Decisao:
        """Score candidate actions and return the safest useful option."""
        candidates: List[AcaoCandidata] = [
            item if isinstance(item, AcaoCandidata) else AcaoCandidata.from_dict(item)
            for item in acoes_candidatas
        ]
        if not candidates:
            return Decisao(None, 0.0, NivelRisco.SEGURO, False, "Nenhuma acao candidata.", 1.0)

        scored = []
        for action in candidates:
            risk = self.classificar_risco(action, estado_mundo or {})
            score = action.prioridade - self.RISK_PENALTY[risk] + action.urgencia - action.custo_recurso
            scored.append((score, action, risk))

        score, chosen, risk = max(scored, key=lambda item: item[0])
        requires_confirmation = self._requires_confirmation(chosen, risk)
        reason = self._reason(chosen, risk, requires_confirmation)
        confidence = max(0.0, min(1.0, chosen.prioridade - self.RISK_PENALTY[risk] / 2))
        return Decisao(chosen, score, risk, requires_confirmation, reason, confidence)

    def classificar_risco(self, action: AcaoCandidata, estado_mundo: Dict) -> NivelRisco:
        """Classify risk, preferring the C++ quick core when available."""
        native = assess_action_risk(action.acao, action.parametros)
        if native and native.get("risk") in {item.value for item in NivelRisco}:
            return NivelRisco(str(native["risk"]))

        name = action.acao
        params = action.parametros
        if name == "buscar_arquivo":
            return NivelRisco.SEGURO
        if name in {"abrir_arquivo", "controlar_luz"}:
            return NivelRisco.BAIXO
        if name == "executar_programa":
            program = str(params.get("programa", "")).lower()
            if any(token in program for token in ["&", "|", ";", "<", ">", "`"]):
                return NivelRisco.CRITICO
            return NivelRisco.BAIXO
        if name == "dume_emergency_stop":
            return NivelRisco.SEGURO
        if name == "dume_command":
            command = str(params.get("command", "")).lower()
            if command in {"status", "capabilities", "diagnostics", "emergency_stop", "stop"}:
                return NivelRisco.SEGURO
            if command in {"home", "open_gripper"}:
                return NivelRisco.MEDIO
            return NivelRisco.ALTO
        if name in {"enviar_email", "mover_braco"}:
            return NivelRisco.ALTO
        if estado_mundo.get("pessoas_presentes") and name.startswith("robot"):
            return NivelRisco.CRITICO
        return NivelRisco.MEDIO

    def _requires_confirmation(self, action: AcaoCandidata, risk: NivelRisco) -> bool:
        if risk == NivelRisco.CRITICO:
            return True
        if risk == NivelRisco.ALTO:
            return True
        if action.irreversivel and risk in {NivelRisco.MEDIO, NivelRisco.ALTO}:
            return True
        return False

    def _reason(self, action: AcaoCandidata, risk: NivelRisco, confirmation: bool) -> str:
        if confirmation:
            return f"Acao '{action.acao}' classificada como risco {risk.value}; aguardando confirmacao humana."
        return f"Acao '{action.acao}' classificada como risco {risk.value}; autorizada pelo MVP seguro."


decision_engine = DecisionEngine()
