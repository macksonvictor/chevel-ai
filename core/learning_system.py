"""Experience buffer and behavior optimizer for CHEVEL."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from utils.config_manager import get_config


@dataclass
class Episodio:
    id: Optional[int]
    timestamp: str
    contexto: Dict
    acao: str
    parametros: Dict
    resultado: str
    recompensa: float
    observacoes: str = ""

    def to_record(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "contexto": self.contexto,
            "acao": self.acao,
            "parametros": self.parametros,
            "resultado": self.resultado,
            "recompensa": self.recompensa,
            "observacoes": self.observacoes,
        }


class ExperienceBuffer:
    """Persistent action-result memory."""

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
                CREATE TABLE IF NOT EXISTS episodios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    contexto TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    parametros TEXT,
                    resultado TEXT NOT NULL,
                    recompensa REAL NOT NULL,
                    observacoes TEXT
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS behavior_scores (
                    acao TEXT NOT NULL,
                    contexto_hash TEXT NOT NULL,
                    sucesso_count INTEGER DEFAULT 0,
                    falha_count INTEGER DEFAULT 0,
                    recompensa_media REAL DEFAULT 0.0,
                    atualizado_em TEXT NOT NULL,
                    PRIMARY KEY (acao, contexto_hash)
                )
                """
            )
            self.conn.commit()

    def registrar(self, episodio: Episodio) -> int:
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO episodios
                (timestamp, contexto, acao, parametros, resultado, recompensa, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episodio.timestamp,
                    json.dumps(episodio.contexto, ensure_ascii=False),
                    episodio.acao,
                    json.dumps(episodio.parametros, ensure_ascii=False),
                    episodio.resultado,
                    episodio.recompensa,
                    episodio.observacoes,
                ),
            )
            self.conn.commit()
            episodio.id = int(cursor.lastrowid)
            return episodio.id

    def recentes(self, limite: int = 20) -> List[Dict]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT id, timestamp, acao, resultado, recompensa, observacoes
                FROM episodios
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite,),
            ).fetchall()
            return [dict(row) for row in rows]

    def metricas(self) -> Dict:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    AVG(recompensa) AS recompensa_media,
                    SUM(CASE WHEN resultado = 'sucesso' THEN 1 ELSE 0 END) AS sucessos
                FROM episodios
                """
            ).fetchone()
            total = int(row["total"] or 0)
            return {
                "total": total,
                "recompensa_media": float(row["recompensa_media"] or 0.0),
                "taxa_sucesso": (float(row["sucessos"] or 0) / total) if total else 1.0,
            }

    def close(self) -> None:
        with self._lock:
            self.conn.close()


class BehaviorOptimizer:
    """Learns lightweight action preferences from episodes."""

    def __init__(self, buffer: ExperienceBuffer):
        self.buffer = buffer

    def aprender_com_episodio(self, episodio: Episodio) -> None:
        contexto_hash = self._context_hash(episodio.contexto)
        success = 1 if episodio.resultado == "sucesso" else 0
        failure = 0 if success else 1
        with self.buffer._lock:
            row = self.buffer.conn.execute(
                """
                SELECT sucesso_count, falha_count, recompensa_media
                FROM behavior_scores
                WHERE acao = ? AND contexto_hash = ?
                """,
                (episodio.acao, contexto_hash),
            ).fetchone()
            now = datetime.now().isoformat()
            if row:
                total = int(row["sucesso_count"]) + int(row["falha_count"])
                new_total = total + 1
                avg = ((float(row["recompensa_media"]) * total) + episodio.recompensa) / new_total
                self.buffer.conn.execute(
                    """
                    UPDATE behavior_scores
                    SET sucesso_count = sucesso_count + ?,
                        falha_count = falha_count + ?,
                        recompensa_media = ?,
                        atualizado_em = ?
                    WHERE acao = ? AND contexto_hash = ?
                    """,
                    (success, failure, avg, now, episodio.acao, contexto_hash),
                )
            else:
                self.buffer.conn.execute(
                    """
                    INSERT INTO behavior_scores
                    (acao, contexto_hash, sucesso_count, falha_count, recompensa_media, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (episodio.acao, contexto_hash, success, failure, episodio.recompensa, now),
                )
            self.buffer.conn.commit()

    def recomendar_acao(self, acoes_candidatas: Iterable[str], contexto: Dict) -> Optional[str]:
        candidates = list(acoes_candidatas)
        if not candidates:
            return None
        contexto_hash = self._context_hash(contexto)
        with self.buffer._lock:
            rows = self.buffer.conn.execute(
                """
                SELECT acao, recompensa_media
                FROM behavior_scores
                WHERE contexto_hash = ?
                """,
                (contexto_hash,),
            ).fetchall()
        scores = {row["acao"]: float(row["recompensa_media"]) for row in rows}
        return max(candidates, key=lambda action: scores.get(action, 0.0))

    def _context_hash(self, contexto: Dict) -> str:
        compact = json.dumps(contexto, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(compact.encode("utf-8")).hexdigest()[:16]


experience_buffer = ExperienceBuffer()
behavior_optimizer = BehaviorOptimizer(experience_buffer)
