"""IoT controller stubs for the CHEVEL MVP."""

from __future__ import annotations

from typing import Dict


class IoTController:
    """Stubbed IoT controller until real integrations are configured."""

    def controlar_luz(self, entidade: str = "light.sala", acao: str = "toggle") -> Dict:
        return {
            "status": "stub",
            "mensagem": f"IoT ainda nao configurado. Pedido: {acao} em {entidade}",
        }

    def controlar_braco(self, comando: Dict) -> Dict:
        return {
            "status": "stub",
            "mensagem": "Controle robotico ainda nao configurado.",
            "comando": comando,
        }


iot_controller = IoTController()

