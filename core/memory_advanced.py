"""Procedural memory and forgetting maintenance for CHEVEL."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.config_manager import get_config


@dataclass
class Passo:
    ordem: int
    descricao: str
    acao: str
    parametros: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "ordem": self.ordem,
            "descricao": self.descricao,
            "acao": self.acao,
            "parametros": self.parametros,
        }


@dataclass
class Procedimento:
    nome: str
    descricao: str
    passos: List[Passo]
    relevancia: float = 0.8

    def to_dict(self) -> Dict:
        return {
            "nome": self.nome,
            "descricao": self.descricao,
            "passos": [passo.to_dict() for passo in self.passos],
            "relevancia": self.relevancia,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Procedimento":
        steps = [
            Passo(
                ordem=int(item["ordem"]),
                descricao=str(item["descricao"]),
                acao=str(item["acao"]),
                parametros=dict(item.get("parametros", {})),
            )
            for item in json.loads(row["passos"])
        ]
        return cls(
            nome=row["nome"],
            descricao=row["descricao"],
            passos=steps,
            relevancia=float(row["relevancia"]),
        )


class MemoriaProcedural:
    """SQLite-backed procedural memory."""

    def __init__(self, db_path: str | Path | None = None):
        config = get_config()
        self.db_path = Path(db_path or config.memory_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()

    def _init_database(self) -> None:
        with self._lock:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS procedimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    descricao TEXT NOT NULL,
                    passos TEXT NOT NULL,
                    relevancia REAL DEFAULT 0.8,
                    uso_count INTEGER DEFAULT 0,
                    arquivado INTEGER DEFAULT 0,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            self.conn.commit()

    def salvar(self, procedimento: Procedimento) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO procedimentos
                (nome, descricao, passos, relevancia, uso_count, arquivado, atualizado_em)
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    COALESCE((SELECT uso_count FROM procedimentos WHERE nome = ?), 0),
                    0,
                    ?
                )
                """,
                (
                    procedimento.nome,
                    procedimento.descricao,
                    json.dumps([step.to_dict() for step in procedimento.passos], ensure_ascii=False),
                    procedimento.relevancia,
                    procedimento.nome,
                    datetime.now().isoformat(),
                ),
            )
            self.conn.commit()

    def recuperar(self, nome: str) -> Optional[Procedimento]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT nome, descricao, passos, relevancia
                FROM procedimentos
                WHERE nome = ? AND arquivado = 0
                """,
                (nome,),
            ).fetchone()
            if not row:
                return None
            self.conn.execute(
                """
                UPDATE procedimentos
                SET uso_count = uso_count + 1,
                    relevancia = MIN(1.0, relevancia + 0.05),
                    atualizado_em = ?
                WHERE nome = ?
                """,
                (datetime.now().isoformat(), nome),
            )
            self.conn.commit()
            return Procedimento.from_row(row)

    def listar(self, incluir_arquivados: bool = False) -> List[Dict]:
        query = (
            "SELECT nome, descricao, relevancia, uso_count, arquivado, atualizado_em "
            "FROM procedimentos"
        )
        if not incluir_arquivados:
            query += " WHERE arquivado = 0"
        query += " ORDER BY relevancia DESC, atualizado_em DESC"
        with self._lock:
            return [dict(row) for row in self.conn.execute(query).fetchall()]

    def close(self) -> None:
        with self._lock:
            self.conn.close()


class EsquecimentoInteligente:
    """Maintenance cycle for low-value procedural memories."""

    def __init__(self, memoria: MemoriaProcedural):
        self.memoria = memoria

    def ciclo_manutencao(self) -> Dict:
        with self.memoria._lock:
            cursor = self.memoria.conn.cursor()
            cursor.execute(
                """
                UPDATE procedimentos
                SET relevancia = CASE
                    WHEN uso_count >= 3 THEN 1.0
                    WHEN uso_count = 0 THEN MAX(0.0, relevancia - 0.05)
                    ELSE MIN(1.0, relevancia + 0.02)
                END,
                atualizado_em = ?
                """,
                (datetime.now().isoformat(),),
            )
            cursor.execute(
                """
                UPDATE procedimentos
                SET arquivado = 1
                WHERE relevancia < 0.10 AND uso_count = 0
                """
            )
            self.memoria.conn.commit()
            rows = self.memoria.conn.execute(
                "SELECT COUNT(*) AS total, SUM(arquivado) AS arquivados FROM procedimentos"
            ).fetchone()
            return {
                "status": "ok",
                "total": int(rows["total"] or 0),
                "arquivados": int(rows["arquivados"] or 0),
            }


memoria_procedural = MemoriaProcedural()
esquecimento = EsquecimentoInteligente(memoria_procedural)
