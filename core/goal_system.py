"""Persistent goals and proactive suggestions for CHEVEL."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from utils.config_manager import get_config


class TipoMeta(str, Enum):
    ENERGIA = "energia"
    SEGURANCA = "seguranca"
    APRENDIZADO = "aprendizado"
    ORGANIZACAO = "organizacao"
    CUSTOM = "custom"


@dataclass
class Meta:
    id: Optional[int]
    nome: str
    descricao: str
    tipo: TipoMeta
    prioridade: int
    criterio: str
    status: str = "ativa"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "tipo": self.tipo.value,
            "prioridade": self.prioridade,
            "criterio": self.criterio,
            "status": self.status,
        }


class GoalSystem:
    """Stores long-running goals and proposes safe proactive actions."""

    def __init__(self, db_path: str | Path | None = None):
        config = get_config()
        self.db_path = Path(db_path or config.memory_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()
        self._ensure_default_goals()

    def _init_database(self) -> None:
        with self._lock:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    descricao TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    prioridade INTEGER NOT NULL,
                    criterio TEXT NOT NULL,
                    status TEXT NOT NULL,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            self.conn.commit()

    def adicionar_meta(
        self,
        nome: str,
        descricao: str,
        tipo: TipoMeta,
        prioridade: int,
        criterio: str,
    ) -> Meta:
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT OR REPLACE INTO metas
                (nome, descricao, tipo, prioridade, criterio, status, criado_em, atualizado_em)
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    COALESCE((SELECT status FROM metas WHERE nome = ?), 'ativa'),
                    COALESCE((SELECT criado_em FROM metas WHERE nome = ?), ?),
                    ?
                )
                """,
                (nome, descricao, tipo.value, prioridade, criterio, nome, nome, now, now),
            )
            self.conn.commit()
            return Meta(cursor.lastrowid or None, nome, descricao, tipo, prioridade, criterio)

    def listar_metas(self, status: str = "ativa") -> List[Dict]:
        query = (
            "SELECT id, nome, descricao, tipo, prioridade, criterio, status "
            "FROM metas"
        )
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY prioridade DESC, atualizado_em DESC"
        with self._lock:
            return [dict(row) for row in self.conn.execute(query, params).fetchall()]

    def gerar_submetas(self, meta: Meta | Dict) -> List[Dict]:
        tipo = meta.tipo if isinstance(meta, Meta) else meta.get("tipo")
        if isinstance(tipo, TipoMeta):
            tipo = tipo.value
        if tipo == TipoMeta.ENERGIA.value:
            return [{"acao": "monitorar_bateria"}, {"acao": "sugerir_recarga"}]
        if tipo == TipoMeta.SEGURANCA.value:
            return [{"acao": "verificar_pessoas"}, {"acao": "bloquear_risco"}]
        if tipo == TipoMeta.APRENDIZADO.value:
            return [{"acao": "processar_episodios"}, {"acao": "consolidar_memoria"}]
        return [{"acao": "avaliar_estado"}, {"acao": "sugerir_proximo_passo"}]

    def proxima_acao_proativa(self, estado_mundo: Dict) -> Optional[Dict]:
        sistema = estado_mundo.get("sistema", {})
        pessoas = estado_mundo.get("pessoas_presentes", [])
        battery = sistema.get("bateria")
        try:
            battery_value = float(battery)
        except (TypeError, ValueError):
            battery_value = None
        if battery_value is not None and battery_value < 15:
            return {
                "meta_nome": "Gestao de energia",
                "acao_sugerida": {"acao": "pausar_operacoes", "parametros": {"motivo": "bateria_baixa"}},
                "prioridade": 10,
            }
        if pessoas:
            return {
                "meta_nome": "Manter zona segura",
                "acao_sugerida": {"acao": "monitorar_seguranca", "parametros": {"pessoas": pessoas}},
                "prioridade": 9,
            }
        return None

    def _ensure_default_goals(self) -> None:
        defaults = [
            ("Gestao de energia", "Manter bateria acima de 15%.", TipoMeta.ENERGIA, 10, "bateria > 15"),
            ("Manter zona segura", "Evitar humanos em risco.", TipoMeta.SEGURANCA, 10, "sem_humanos_em_risco"),
            ("Aprendizado continuo", "Processar episodios e melhorar comportamento.", TipoMeta.APRENDIZADO, 7, "episodios_processados"),
            ("Manter ambiente organizado", "Verificar periodicamente a organizacao.", TipoMeta.ORGANIZACAO, 5, "ambiente_organizado"),
        ]
        for item in defaults:
            self.adicionar_meta(*item)

    def close(self) -> None:
        with self._lock:
            self.conn.close()


goal_system = GoalSystem()
