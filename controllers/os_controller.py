"""Safe operating-system actions for CHEVEL MVP."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List

from utils.security import (
    SecurityError,
    clean_text,
    ensure_existing_path,
    get_allowed_program_command,
    safe_search_roots,
)


class OSController:
    """Controller for local, allowlisted OS actions."""

    def abrir_arquivo(self, caminho: str) -> Dict:
        """Open a local file or folder using the OS default handler."""
        try:
            path = ensure_existing_path(caminho)
            if hasattr(os, "startfile"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)], shell=False)
            return {
                "status": "success",
                "mensagem": f"Arquivo aberto: {path}",
                "caminho": str(path),
            }
        except SecurityError as exc:
            return {"status": "error", "mensagem": str(exc)}
        except Exception as exc:
            return {"status": "error", "mensagem": f"Falha ao abrir: {exc}"}

    def executar_programa(self, programa: str) -> Dict:
        """Execute an allowlisted program without shell expansion."""
        try:
            command = get_allowed_program_command(programa)
            subprocess.Popen(command, shell=False)
            return {
                "status": "success",
                "mensagem": f"Programa iniciado: {programa}",
                "comando": command,
            }
        except SecurityError as exc:
            return {"status": "error", "mensagem": str(exc)}
        except Exception as exc:
            return {"status": "error", "mensagem": f"Falha ao executar: {exc}"}

    def buscar_arquivos(
        self,
        nome: str,
        limite: int = 20,
        roots: List[Path] | None = None,
    ) -> List[Dict]:
        """Search files by name in bounded safe roots."""
        query = clean_text(nome).lower()
        if not query:
            return []

        resultados: List[Dict] = []
        for root in safe_search_roots(roots):
            for current_root, dirnames, filenames in os.walk(root):
                dirnames[:] = [
                    item for item in dirnames
                    if item not in {".git", ".venv", "__pycache__", "node_modules"}
                ]
                names = [(filename, "file") for filename in filenames]
                names.extend((dirname, "directory") for dirname in dirnames)
                for item_name, item_type in names:
                    if query in item_name.lower():
                        path = Path(current_root) / item_name
                        resultados.append({
                            "nome": item_name,
                            "tipo": item_type,
                            "caminho": str(path),
                        })
                        if len(resultados) >= limite:
                            return resultados
        return resultados


os_controller = OSController()

