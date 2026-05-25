"""Safe simulated bridge for the Dum-E/U robotic platform."""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from datetime import datetime
from typing import Dict, List


class DumeController:
    """Control contract for Dum-E/U, running in safe simulation by default."""

    SAFE_COMMANDS = {"status", "capabilities", "diagnostics"}
    EMERGENCY_COMMANDS = {"emergency_stop", "stop", "parada_emergencia", "parar_tudo"}
    MOTION_COMMANDS = {
        "home",
        "move_arm",
        "move_joint",
        "move_pose",
        "open_gripper",
        "close_gripper",
        "set_gripper",
        "navigate",
        "pick",
        "place",
        "deliver",
        "follow_trajectory",
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sequence = 0
        self._state = {
            "platform": "Dum-E/U",
            "mode": "simulation",
            "hardware_connected": False,
            "emergency_stop": False,
            "last_command": None,
            "joints": [0.0] * 7,
            "pose": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.42,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
            "gripper": {
                "state": "open",
                "force": 0.0,
            },
            "base": {
                "x": 0.0,
                "y": 0.0,
                "theta": 0.0,
                "velocity": 0.0,
            },
            "battery": {
                "percent": 100.0,
                "voltage": 22.2,
                "current": 0.0,
            },
            "safety": {
                "thermal_ok": True,
                "current_ok": True,
                "human_in_arm_zone": False,
                "requires_human_confirmation": True,
            },
            "updated_at": datetime.now().isoformat(),
        }

    def capabilities(self) -> Dict:
        """Return the Dum-E/U contract CHEVEL can target."""
        return {
            "platform": "Dum-E/U",
            "mode": self._state["mode"],
            "hardware_connected": self._state["hardware_connected"],
            "commands": sorted(self.SAFE_COMMANDS | self.EMERGENCY_COMMANDS | self.MOTION_COMMANDS),
            "telemetry": [
                "joints",
                "pose",
                "gripper",
                "base",
                "battery",
                "safety",
            ],
            "future_adapters": [
                "ROS 2",
                "REST hardware API",
                "serial/Arduino",
                "Jetson perception stack",
            ],
            "safety_policy": {
                "emergency_stop": "always_allowed",
                "read_only": "allowed",
                "motion": "requires_confirmation",
                "hardware": "disabled_until_adapter_configured",
            },
        }

    def status(self) -> Dict:
        """Return a copy of the current simulated platform state."""
        with self._lock:
            return deepcopy(self._state)

    def telemetry(self) -> Dict:
        """Return one telemetry frame for API/WebSocket clients."""
        with self._lock:
            self._sequence += 1
            payload = deepcopy(self._state)
            payload["sequence"] = self._sequence
            payload["timestamp"] = time.time()
            return payload

    def execute_command(
        self,
        command: str,
        parameters: Dict | None = None,
        *,
        confirm: bool = False,
        source: str = "api",
    ) -> Dict:
        """Execute a safe simulated command or request human confirmation."""
        normalized = self._normalize(command)
        params = dict(parameters or {})
        risk = self.command_risk(normalized)

        if normalized in self.EMERGENCY_COMMANDS:
            return self.emergency_stop(source=source, reason=params.get("reason", "manual"))

        if normalized not in self.SAFE_COMMANDS and normalized not in self.MOTION_COMMANDS:
            return {
                "status": "error",
                "mensagem": f"Comando Dum-E/U desconhecido: {command}",
                "command": normalized,
                "risk": "medio",
            }

        if self.requires_confirmation(normalized, confirm):
            return {
                "status": "requires_confirmation",
                "mensagem": (
                    "Comando fisico do Dum-E/U bloqueado ate confirmacao humana. "
                    "No MVP ele roda em simulacao, mas a regra de seguranca ja fica ativa."
                ),
                "command": normalized,
                "risk": risk,
                "requires_confirmation": True,
                "parameters": params,
            }

        if normalized in self.SAFE_COMMANDS:
            return {
                "status": "success",
                "mensagem": "Estado Dum-E/U consultado.",
                "command": normalized,
                "risk": risk,
                "state": self.status(),
            }

        with self._lock:
            result = self._apply_simulated_motion(normalized, params, source)
            self._state["updated_at"] = datetime.now().isoformat()
            return result

    def emergency_stop(self, *, source: str = "api", reason: str = "manual") -> Dict:
        """Put Dum-E/U into a safe stopped state immediately."""
        with self._lock:
            self._state["emergency_stop"] = True
            self._state["mode"] = "safe_stop"
            self._state["base"]["velocity"] = 0.0
            self._state["battery"]["current"] = 0.0
            self._state["last_command"] = {
                "command": "emergency_stop",
                "source": source,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
            self._state["updated_at"] = datetime.now().isoformat()
            return {
                "status": "success",
                "mensagem": "Parada de emergencia Dum-E/U acionada em modo seguro.",
                "command": "emergency_stop",
                "risk": "seguro",
                "state": self.status(),
            }

    def command_risk(self, command: str) -> str:
        """Classify Dum-E/U command risk before execution."""
        normalized = self._normalize(command)
        if normalized in self.EMERGENCY_COMMANDS or normalized in self.SAFE_COMMANDS:
            return "seguro"
        if normalized in {"home", "open_gripper"}:
            return "medio"
        if normalized in self.MOTION_COMMANDS:
            return "alto"
        return "medio"

    def requires_confirmation(self, command: str, confirm: bool) -> bool:
        """Return True when a command must be confirmed by a human."""
        normalized = self._normalize(command)
        if normalized in self.SAFE_COMMANDS or normalized in self.EMERGENCY_COMMANDS:
            return False
        return normalized in self.MOTION_COMMANDS and not confirm

    def summary(self) -> Dict:
        """Compact health summary for CHEVEL health checks."""
        state = self.status()
        return {
            "platform": state["platform"],
            "mode": state["mode"],
            "hardware_connected": state["hardware_connected"],
            "emergency_stop": state["emergency_stop"],
            "battery_percent": state["battery"]["percent"],
        }

    def _apply_simulated_motion(self, command: str, params: Dict, source: str) -> Dict:
        if command == "home":
            self._state["joints"] = [0.0] * 7
            self._state["pose"].update({"x": 0.0, "y": 0.0, "z": 0.42, "roll": 0.0, "pitch": 0.0, "yaw": 0.0})
        elif command in {"move_joint", "follow_trajectory"}:
            joints = params.get("joints") or params.get("angulos")
            if not isinstance(joints, list) or len(joints) != 7:
                return {
                    "status": "error",
                    "mensagem": "Comando de juntas precisa de 7 valores.",
                    "command": command,
                }
            self._state["joints"] = [float(item) for item in joints]
        elif command in {"move_pose", "move_arm"}:
            for key in ["x", "y", "z", "roll", "pitch", "yaw"]:
                if key in params:
                    self._state["pose"][key] = float(params[key])
        elif command in {"open_gripper", "close_gripper", "set_gripper"}:
            if command == "open_gripper":
                self._state["gripper"].update({"state": "open", "force": 0.0})
            elif command == "close_gripper":
                self._state["gripper"].update({"state": "closed", "force": float(params.get("force", 50.0))})
            else:
                self._state["gripper"].update({
                    "state": str(params.get("state", self._state["gripper"]["state"])),
                    "force": float(params.get("force", self._state["gripper"]["force"])),
                })
        elif command == "navigate":
            self._state["base"].update({
                "x": float(params.get("x", self._state["base"]["x"])),
                "y": float(params.get("y", self._state["base"]["y"])),
                "theta": float(params.get("theta", self._state["base"]["theta"])),
                "velocity": 0.0,
            })

        self._state["mode"] = "simulation"
        self._state["emergency_stop"] = False
        self._state["last_command"] = {
            "command": command,
            "parameters": params,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "simulated": True,
        }
        return {
            "status": "success",
            "mensagem": f"Comando Dum-E/U simulado: {command}.",
            "command": command,
            "risk": self.command_risk(command),
            "simulated": True,
            "state": self.status(),
        }

    def _normalize(self, command: str) -> str:
        return str(command or "").strip().lower().replace("-", "_").replace(" ", "_")


dume_controller = DumeController()
