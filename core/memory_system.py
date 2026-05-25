"""SQLite memory system for CHEVEL."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.config_manager import get_config


class CHEVELMemory:
    """Local long-term memory backed by SQLite."""

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
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    chevel TEXT NOT NULL,
                    contexto TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conhecimento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    confianca REAL DEFAULT 1.0,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(categoria, chave)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS preferencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    item TEXT NOT NULL,
                    valor REAL DEFAULT 0.0,
                    observacoes TEXT,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    dados TEXT
                )
                """
            )
            self.conn.commit()

    def salvar_conversa(
        self,
        usuario: str,
        chevel: str,
        contexto: Optional[Dict] = None,
    ) -> int:
        """Save a conversation turn."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversas (timestamp, usuario, chevel, contexto)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    usuario,
                    chevel,
                    json.dumps(contexto, ensure_ascii=False) if contexto else None,
                ),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def buscar_conversas_recentes(self, limite: int = 10) -> List[Dict]:
        """Return recent conversations, newest first."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, usuario, chevel, contexto
                FROM conversas
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limite,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def salvar_conhecimento(
        self,
        categoria: str,
        chave: str,
        valor: str,
        confianca: float = 1.0,
    ) -> None:
        """Save or replace a knowledge fact."""
        with self._lock:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO conhecimento
                (categoria, chave, valor, confianca, atualizado_em)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    categoria,
                    chave.lower(),
                    valor,
                    confianca,
                    datetime.now().isoformat(),
                ),
            )
            self.conn.commit()

    def buscar_conhecimento(
        self,
        categoria: str | None = None,
        chave: str | None = None,
    ) -> List[Dict]:
        """Search knowledge facts."""
        query = (
            "SELECT categoria, chave, valor, confianca, atualizado_em "
            "FROM conhecimento WHERE 1=1"
        )
        params = []
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if chave:
            query += " AND chave = ?"
            params.append(chave.lower())

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def aprender_preferencia(
        self,
        tipo: str,
        item: str,
        valor: float,
        observacoes: str | None = None,
    ) -> None:
        """Learn or update a user preference."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, valor FROM preferencias
                WHERE tipo = ? AND item = ?
                """,
                (tipo, item),
            )
            row = cursor.fetchone()
            now = datetime.now().isoformat()
            if row:
                novo_valor = (float(row["valor"]) + float(valor)) / 2.0
                cursor.execute(
                    """
                    UPDATE preferencias
                    SET valor = ?, observacoes = ?, atualizado_em = ?
                    WHERE id = ?
                    """,
                    (novo_valor, observacoes, now, row["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO preferencias
                    (tipo, item, valor, observacoes, atualizado_em)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (tipo, item, valor, observacoes, now),
                )
            self.conn.commit()

    def obter_preferencias(self, tipo: str | None = None) -> List[Dict]:
        """Return learned preferences."""
        with self._lock:
            cursor = self.conn.cursor()
            if tipo:
                cursor.execute(
                    """
                    SELECT tipo, item, valor, observacoes, atualizado_em
                    FROM preferencias
                    WHERE tipo = ?
                    ORDER BY valor DESC
                    """,
                    (tipo,),
                )
            else:
                cursor.execute(
                    """
                    SELECT tipo, item, valor, observacoes, atualizado_em
                    FROM preferencias
                    ORDER BY atualizado_em DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]

    def registrar_evento(
        self,
        tipo: str,
        descricao: str,
        dados: Optional[Dict] = None,
    ) -> None:
        """Register an important event."""
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO eventos (timestamp, tipo, descricao, dados)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    tipo,
                    descricao,
                    json.dumps(dados, ensure_ascii=False) if dados else None,
                ),
            )
            self.conn.commit()

    def buscar_eventos(self, tipo: str | None = None, limite: int = 20) -> List[Dict]:
        """Return recent events."""
        with self._lock:
            cursor = self.conn.cursor()
            if tipo:
                cursor.execute(
                    """
                    SELECT timestamp, tipo, descricao, dados
                    FROM eventos
                    WHERE tipo = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (tipo, limite),
                )
            else:
                cursor.execute(
                    """
                    SELECT timestamp, tipo, descricao, dados
                    FROM eventos
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limite,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def gerar_contexto_para_llm(self, mensagem_usuario: str) -> Dict:
        """Build a compact context block for the LLM."""
        contexto: Dict[str, object] = {}
        recentes = self.buscar_conversas_recentes(5)
        if recentes:
            contexto["conversas_recentes"] = [
                {
                    "timestamp": row["timestamp"],
                    "usuario": row["usuario"],
                    "chevel": row["chevel"],
                }
                for row in recentes
            ]

        palavras = {
            palavra.strip(".,!?;:").lower()
            for palavra in mensagem_usuario.split()
            if len(palavra.strip(".,!?;:")) > 2
        }
        conhecimento = []
        for palavra in list(palavras)[:8]:
            conhecimento.extend(self.buscar_conhecimento(chave=palavra))
        if conhecimento:
            contexto["conhecimento"] = conhecimento

        eventos = self.buscar_eventos(limite=5)
        if eventos:
            contexto["eventos_recentes"] = eventos
        return contexto

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self.conn.close()


chevel_memory = CHEVELMemory()

