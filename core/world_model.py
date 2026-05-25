"""Internal world model for CHEVEL."""

from __future__ import annotations

import json
import sqlite3
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from utils.config_manager import get_config


@dataclass
class ObjetoMundo:
    """Object tracked by the CHEVEL world model."""

    id: str
    tipo: str
    posicao: Tuple[float, float, float] | None = None
    estado: str = "desconhecido"
    atributos: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "posicao": self.posicao,
            "estado": self.estado,
            "atributos": self.atributos,
        }


@dataclass
class EstadoMundo:
    """Snapshot of CHEVEL's known environment."""

    objetos: Dict[str, ObjetoMundo] = field(default_factory=dict)
    sistema: Dict = field(default_factory=dict)
    ambiente: Dict = field(default_factory=dict)
    pessoas_presentes: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "objetos": {key: value.to_dict() for key, value in self.objetos.items()},
            "sistema": dict(self.sistema),
            "ambiente": dict(self.ambiente),
            "pessoas_presentes": list(self.pessoas_presentes),
            "timestamp": self.timestamp,
        }


class WorldModel:
    """Mutable representation of what CHEVEL knows about the local world."""

    def __init__(self, db_path: str | Path | None = None):
        config = get_config()
        self.db_path = Path(db_path or config.memory_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.estado = EstadoMundo()
        self.historico: List[Dict] = []
        self._init_database()

    def _init_database(self) -> None:
        with self._lock:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    snapshot TEXT NOT NULL
                )
                """
            )
            self.conn.commit()

    def atualizar_sistema(self, chave: str, valor) -> None:
        self._capture_history()
        self.estado.sistema[chave] = valor
        self.estado.timestamp = datetime.now().isoformat()

    def atualizar_ambiente(self, chave: str, valor) -> None:
        self._capture_history()
        self.estado.ambiente[chave] = valor
        self.estado.timestamp = datetime.now().isoformat()

    def atualizar_objeto(self, objeto: ObjetoMundo) -> None:
        self._capture_history()
        self.estado.objetos[objeto.id] = objeto
        self.estado.timestamp = datetime.now().isoformat()

    def registrar_pessoa(self, nome: str) -> None:
        self._capture_history()
        if nome not in self.estado.pessoas_presentes:
            self.estado.pessoas_presentes.append(nome)
        self.estado.timestamp = datetime.now().isoformat()

    def remover_pessoa(self, nome: str) -> None:
        self._capture_history()
        self.estado.pessoas_presentes = [
            item for item in self.estado.pessoas_presentes if item != nome
        ]
        self.estado.timestamp = datetime.now().isoformat()

    def atualizar_por_sensores(self, dados_sensores: Dict | None) -> None:
        if not dados_sensores:
            return
        self._capture_history()
        for key, value in dados_sensores.items():
            if key.startswith("ambiente_"):
                self.estado.ambiente[key.removeprefix("ambiente_")] = value
            elif key in {"temperatura", "luz", "umidade"}:
                self.estado.ambiente[key] = value
            elif key == "pessoa_detectada_zona_braco" and value:
                if "zona_braco" not in self.estado.pessoas_presentes:
                    self.estado.pessoas_presentes.append("zona_braco")
            else:
                self.estado.sistema[key] = value
        self.estado.timestamp = datetime.now().isoformat()

    def ha_pessoas_presentes(self) -> bool:
        return bool(self.estado.pessoas_presentes)

    def o_que_mudou(self) -> Dict:
        if not self.historico:
            return {"status": "sem_historico"}
        previous = self.historico[-1]
        current = self.snapshot()
        changes = {}
        for section in ["sistema", "ambiente", "pessoas_presentes", "objetos"]:
            if previous.get(section) != current.get(section):
                changes[section] = {
                    "antes": previous.get(section),
                    "agora": current.get(section),
                }
        return changes or {"status": "sem_mudancas"}

    def prever_estado_apos(self, objeto_id: str, acao: str) -> Dict:
        objeto = self.estado.objetos.get(objeto_id)
        if not objeto:
            return {"status": "desconhecido", "motivo": "objeto nao encontrado"}
        predicted = objeto.to_dict()
        if acao in {"pegar", "segurar"}:
            predicted["estado"] = "na_garra"
        elif acao in {"soltar", "entregar"}:
            predicted["estado"] = "disponivel"
        return {"status": "previsto", "objeto": predicted, "acao": acao}

    def snapshot(self) -> Dict:
        return self.estado.to_dict()

    def salvar_snapshot(self) -> int:
        snapshot = self.snapshot()
        with self._lock:
            cursor = self.conn.execute(
                """
                INSERT INTO world_snapshots (timestamp, snapshot)
                VALUES (?, ?)
                """,
                (
                    snapshot["timestamp"],
                    json.dumps(snapshot, ensure_ascii=False),
                ),
            )
            self.conn.commit()
            return int(cursor.lastrowid)

    def snapshots_recentes(self, limite: int = 10) -> List[Dict]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT id, timestamp, snapshot
                FROM world_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "snapshot": json.loads(row["snapshot"]),
                }
                for row in rows
            ]

    def resumo(self) -> Dict:
        return {
            "objetos": len(self.estado.objetos),
            "sistema": dict(self.estado.sistema),
            "ambiente": dict(self.estado.ambiente),
            "pessoas_presentes": list(self.estado.pessoas_presentes),
            "timestamp": self.estado.timestamp,
        }

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def _capture_history(self) -> None:
        self.historico.append(deepcopy(self.estado.to_dict()))
        self.historico = self.historico[-50:]


world_model = WorldModel()
