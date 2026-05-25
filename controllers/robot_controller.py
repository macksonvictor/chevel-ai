"""Robotics controller stub for CHEVEL MVP."""

from __future__ import annotations

from typing import Dict


class RobotController:
    """Placeholder for robotic arm integration."""

    def mover(self, parametros: Dict) -> Dict:
        return {
            "status": "stub",
            "mensagem": "Braco robotico ainda nao esta conectado.",
            "parametros": parametros,
        }


robot_controller = RobotController()

