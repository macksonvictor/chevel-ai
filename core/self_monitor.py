"""Self-monitoring and confidence checks for CHEVEL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class ConfidenceReport:
    score: float
    nivel: str
    motivos: List[str]

    def to_dict(self) -> Dict:
        return {"score": self.score, "nivel": self.nivel, "motivos": self.motivos}


class SelfMonitor:
    """Tracks uncertainty, recent failures, and cognitive health."""

    def __init__(self):
        self.confiancas: List[float] = []
        self.falhas: Dict[str, int] = {}

    def avaliar_confianca(self, resposta: str, contexto: Dict | None = None, fontes: Iterable | None = None) -> ConfidenceReport:
        score = 0.82
        motivos = []
        text = resposta or ""
        lower = text.lower()
        if not text.strip():
            score -= 0.5
            motivos.append("resposta_vazia")
        if "nao esta respondendo" in lower or "offline" in lower or "erro" in lower:
            score -= 0.35
            motivos.append("erro_ou_offline")
        if contexto and contexto.get("pesquisa_web"):
            status = contexto["pesquisa_web"].get("status")
            if status == "ok":
                score += 0.08
                motivos.append("contexto_web_ok")
            elif status == "indisponivel":
                score -= 0.15
                motivos.append("contexto_web_indisponivel")
        if fontes:
            score += 0.05
            motivos.append("fontes_presentes")
        score = max(0.0, min(1.0, score))
        nivel = "alto" if score >= 0.75 else "medio" if score >= 0.45 else "baixo"
        self.confiancas.append(score)
        self.confiancas = self.confiancas[-100:]
        return ConfidenceReport(score, nivel, motivos)

    def verificar_e_agir(self, confianca: ConfidenceReport, objetivo: str, contexto: Dict | None = None) -> Dict:
        if confianca.score >= 0.75:
            return {"acao": "prosseguir", "motivo": "confianca_suficiente"}
        if confianca.score >= 0.45:
            return {
                "acao": "alertar_usuario",
                "motivo": "confianca_media",
                "mensagem": "Estou um pouco incerto sobre isso.",
            }
        return {
            "acao": "aguardar_instrucao",
            "motivo": "confianca_baixa",
            "mensagem": "Preciso de ajuda humana antes de continuar.",
        }

    def detectar_falha(self, objetivo: str, resultado_obtido: str, resultado_esperado: str) -> bool:
        failed = resultado_esperado.lower() not in resultado_obtido.lower()
        if failed:
            self.falhas[objetivo] = self.falhas.get(objetivo, 0) + 1
        else:
            self.falhas[objetivo] = 0
        return failed

    def deve_pedir_ajuda(self, objetivo: str) -> bool:
        return self.falhas.get(objetivo, 0) >= 3

    def saude_cognitiva(self) -> Dict:
        avg_conf = sum(self.confiancas) / len(self.confiancas) if self.confiancas else 1.0
        falhas_recentes = sum(1 for value in self.falhas.values() if value > 0)
        if avg_conf >= 0.75 and falhas_recentes == 0:
            status = "saudavel"
        elif avg_conf >= 0.45 and falhas_recentes < 3:
            status = "atencao"
        else:
            status = "critico"
        return {
            "status": status,
            "confianca_media": avg_conf,
            "falhas_recentes": falhas_recentes,
        }


self_monitor = SelfMonitor()
