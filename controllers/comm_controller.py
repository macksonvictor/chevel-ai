"""Communication controller stubs for CHEVEL MVP."""

from __future__ import annotations

from typing import Dict


class CommunicationController:
    """Stubbed communication controller."""

    def enviar_email(
        self,
        destinatario: str,
        assunto: str | None = None,
        corpo: str | None = None,
    ) -> Dict:
        return {
            "status": "needs_input",
            "mensagem": "Email real ainda nao configurado. Informe assunto e corpo.",
            "destinatario": destinatario,
            "assunto": assunto,
            "corpo": corpo,
        }


communication_controller = CommunicationController()

