"""Task decomposition and replanning for CHEVEL."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Subtarefa:
    id: str
    descricao: str
    acao: str
    parametros: Dict = field(default_factory=dict)
    status: str = "pendente"
    tentativas: int = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "descricao": self.descricao,
            "acao": self.acao,
            "parametros": self.parametros,
            "status": self.status,
            "tentativas": self.tentativas,
        }


@dataclass
class PlanoTarefa:
    objetivo: str
    subtarefas: List[Subtarefa]
    criado_em: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "ativo"

    def to_dict(self) -> Dict:
        return {
            "objetivo": self.objetivo,
            "subtarefas": [item.to_dict() for item in self.subtarefas],
            "criado_em": self.criado_em,
            "status": self.status,
        }


class TaskReasoningEngine:
    """Break high-level goals into small actionable tasks."""

    def __init__(self):
        self.planos: List[PlanoTarefa] = []

    def criar_plano(self, objetivo: str, contexto: Dict | None = None) -> PlanoTarefa:
        contexto = contexto or {}
        lower = objetivo.lower()
        if "entreg" in lower:
            template = self._template_entregar(contexto)
        elif "peg" in lower or "pegar" in lower:
            template = self._template_pegar(contexto)
        elif "naveg" in lower or "va ate" in lower or "ir ate" in lower:
            template = self._template_navegar(contexto)
        elif "organiz" in lower:
            template = self._template_organizar(contexto)
        elif "inspec" in lower or "analis" in lower:
            template = self._template_inspecionar(contexto)
        else:
            template = [
                Subtarefa("entender", "Entender objetivo", "raciocinar", {}),
                Subtarefa("executar", "Executar passo seguro", "executar_seguro", {}),
                Subtarefa("confirmar", "Confirmar resultado", "confirmar_resultado", {}),
            ]
        plan = PlanoTarefa(objetivo=objetivo, subtarefas=template)
        self.planos.append(plan)
        self.planos = self.planos[-20:]
        return plan

    def proxima_subtarefa(self, plano: PlanoTarefa) -> Optional[Subtarefa]:
        for item in plano.subtarefas:
            if item.status in {"pendente", "falhou"}:
                return item
        return None

    def registrar_resultado(self, plano: PlanoTarefa, subtarefa: Subtarefa, sucesso: bool) -> None:
        subtarefa.tentativas += 1
        subtarefa.status = "concluida" if sucesso else "falhou"
        if not sucesso and subtarefa.tentativas >= 3:
            self._replanejar(plano, subtarefa)
        if self.verificar_conclusao(plano):
            plano.status = "concluido"

    def verificar_conclusao(self, plano: PlanoTarefa) -> bool:
        return all(item.status == "concluida" for item in plano.subtarefas)

    def _replanejar(self, plano: PlanoTarefa, subtarefa: Subtarefa) -> None:
        subtarefa.status = "bloqueada"
        plano.subtarefas.insert(
            plano.subtarefas.index(subtarefa) + 1,
            Subtarefa(
                id=f"replanejar_{subtarefa.id}",
                descricao=f"Replanejar depois de falha em: {subtarefa.descricao}",
                acao="pedir_ajuda",
                parametros={"motivo": subtarefa.descricao},
            ),
        )

    def _template_pegar(self, contexto: Dict) -> List[Subtarefa]:
        objeto = contexto.get("objeto", "objeto")
        return [
            Subtarefa("localizar", f"Localizar {objeto}", "visao_detectar", {"objeto": objeto}),
            Subtarefa("aproximar", "Aproximar efetuador", "braco_mover", {"objeto": objeto}),
            Subtarefa("pegar", f"Pegar {objeto}", "garra_fechar", {"objeto": objeto}),
            Subtarefa("verificar", "Verificar posse", "verificar_estado", {"esperado": "na_garra"}),
        ]

    def _template_navegar(self, contexto: Dict) -> List[Subtarefa]:
        destino = contexto.get("destino", "destino")
        return [
            Subtarefa("localizar_destino", "Localizar destino", "mapa_localizar", {"destino": destino}),
            Subtarefa("planejar_rota", "Planejar rota", "rota_planejar", {"destino": destino}),
            Subtarefa("executar_rota", "Executar rota", "navegar", {"destino": destino}),
            Subtarefa("confirmar_chegada", "Confirmar chegada", "confirmar_resultado", {}),
        ]

    def _template_entregar(self, contexto: Dict) -> List[Subtarefa]:
        objeto = contexto.get("objeto", "objeto")
        destinatario = contexto.get("destinatario", "usuario")
        return self._template_pegar(contexto) + [
            Subtarefa("ir_ate_destinatario", "Ir ate destinatario", "navegar", {"destino": destinatario}),
            Subtarefa("apresentar", "Apresentar objeto", "braco_mover", {"pose": "entrega"}),
            Subtarefa("soltar", f"Soltar {objeto}", "garra_abrir", {"objeto": objeto}),
        ]

    def _template_organizar(self, contexto: Dict) -> List[Subtarefa]:
        area = contexto.get("area", "ambiente")
        return [
            Subtarefa("mapear", "Mapear itens", "visao_mapear", {"area": area}),
            Subtarefa("categorizar", "Categorizar itens", "categorizar", {"area": area}),
            Subtarefa("reposicionar", "Reposicionar itens", "reposicionar", {"area": area}),
            Subtarefa("confirmar", "Confirmar organizacao", "confirmar_resultado", {}),
        ]

    def _template_inspecionar(self, contexto: Dict) -> List[Subtarefa]:
        alvo = contexto.get("alvo", "alvo")
        return [
            Subtarefa("posicionar_camera", "Posicionar camera", "camera_posicionar", {"alvo": alvo}),
            Subtarefa("capturar", "Capturar imagem", "camera_capturar", {"alvo": alvo}),
            Subtarefa("analisar", "Analisar captura", "visao_analisar", {"alvo": alvo}),
            Subtarefa("relatar", "Relatar achados", "responder", {}),
        ]


task_engine = TaskReasoningEngine()
