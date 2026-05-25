"""Safe 5-DOF robotic arm controller for CHEVEL.

The controller is hardware-ready but defaults to simulation. It converts
cartesian targets into servo angles, validates every angle, and can send the
result to an Arduino Mega serial firmware when a port is configured.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from utils.security import (
    DEFAULT_SERVO_LIMITS,
    SecurityError,
    ServoLimit,
    validate_cartesian_workspace,
    validate_servo_angles,
)
from utils.config_manager import get_config

try:
    import serial
except Exception:  # pragma: no cover - depends on local hardware package
    serial = None


@dataclass(frozen=True)
class ArmGeometry:
    """Basic dimensions for a small 5-servo arm, in millimeters."""

    base_height: float = 55.0
    shoulder_to_elbow: float = 105.0
    elbow_to_wrist: float = 105.0
    wrist_to_tool: float = 55.0


@dataclass
class RobotState:
    """Current simulated/last-commanded robot state."""

    connected: bool = False
    simulated: bool = True
    emergency_stop: bool = False
    angles: List[float] = field(default_factory=lambda: [90.0, 90.0, 90.0, 90.0, 90.0])
    last_command: str = "boot"
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "connected": self.connected,
            "simulated": self.simulated,
            "emergency_stop": self.emergency_stop,
            "angles": list(self.angles),
            "last_command": self.last_command,
            "updated_at": self.updated_at,
        }


class RobotController:
    """Convert CHEVEL robot commands into safe servo-level instructions."""

    def __init__(
        self,
        geometry: ArmGeometry | None = None,
        limits: Sequence[ServoLimit] | None = None,
        port: str | None = None,
        baudrate: int | None = None,
        simulate: bool | None = None,
    ):
        config = get_config()
        configured_port = port if port is not None else config.robot_arm_port
        configured_baudrate = int(baudrate or config.robot_arm_baudrate)
        configured_simulate = config.robot_arm_simulate if simulate is None else simulate

        self.geometry = geometry or ArmGeometry()
        self.limits = list(limits or DEFAULT_SERVO_LIMITS)
        self.port = configured_port
        self.baudrate = configured_baudrate
        self.simulate = configured_simulate or not configured_port
        self.state = RobotState(simulated=self.simulate)
        self._serial = None
        if configured_port and not self.simulate:
            self.connect(configured_port, configured_baudrate)

    def connect(self, port: str, baudrate: int | None = None) -> Dict:
        """Open the serial connection to the Arduino Mega firmware."""
        if serial is None:
            raise SecurityError("pyserial nao esta instalado. Instale pyserial para usar hardware real.")
        self.port = port
        self.baudrate = int(baudrate or self.baudrate)
        self._serial = serial.Serial(self.port, self.baudrate, timeout=2)
        time.sleep(2.0)
        self.simulate = False
        self.state.connected = True
        self.state.simulated = False
        return self.status()

    def status(self) -> Dict:
        """Return current controller state."""
        return {
            "status": "online",
            "platform": "CHEVEL 5DOF arm",
            "backend": "serial" if self._serial else "simulation",
            "geometry": self.geometry.__dict__,
            "limits": [limit.__dict__ for limit in self.limits],
            "state": self.state.to_dict(),
        }

    def home(self) -> Dict:
        """Move to the configured safe home pose."""
        return self.send_angles([limit.home_angle for limit in self.limits], command="HOME")

    def emergency_stop(self, reason: str = "manual") -> Dict:
        """Stop motion immediately and tell firmware to detach servos if connected."""
        self.state.emergency_stop = True
        self.state.last_command = f"EMERGENCY_STOP:{reason}"
        self.state.updated_at = time.time()
        if self._serial:
            self._write_line("STOP")
        return {"status": "success", "reason": reason, "state": self.state.to_dict()}

    def clear_emergency(self) -> Dict:
        """Re-arm the controller after a human has checked the robot."""
        self.state.emergency_stop = False
        self.state.last_command = "ARM"
        self.state.updated_at = time.time()
        if self._serial:
            self._write_line("ARM")
        return self.status()

    def mover(self, parametros: Dict) -> Dict:
        """Compatibility entrypoint used by CHEVEL actions."""
        if "angles" in parametros:
            return self.send_angles(parametros["angles"])
        if {"x", "y", "z"}.issubset(parametros):
            return self.move_cartesian(
                float(parametros["x"]),
                float(parametros["y"]),
                float(parametros["z"]),
                float(parametros.get("wrist", 0.0)),
                float(parametros.get("gripper", 90.0)),
            )
        if parametros.get("acao") == "home":
            return self.home()
        return {
            "status": "error",
            "mensagem": "Parametros roboticos insuficientes. Use angles ou x/y/z.",
            "parametros": parametros,
        }

    def move_cartesian(
        self,
        x: float,
        y: float,
        z: float,
        wrist_pitch: float = 0.0,
        gripper: float = 90.0,
    ) -> Dict:
        """Solve inverse kinematics and send the resulting safe servo angles."""
        angles = self.cartesian_to_servo_angles(x, y, z, wrist_pitch, gripper)
        result = self.send_angles(angles, command="MOVE")
        result["target"] = {"x": x, "y": y, "z": z}
        return result

    def cartesian_to_servo_angles(
        self,
        x: float,
        y: float,
        z: float,
        wrist_pitch: float = 0.0,
        gripper: float = 90.0,
    ) -> List[float]:
        """Analytical IK for a 5-DOF hobby arm, with optional library slot.

        The controller exposes a clean IK boundary so a heavier solver such as
        IKPy can be plugged in later without changing the serial protocol.
        """
        validate_cartesian_workspace(x, y, z)

        base = math.degrees(math.atan2(y, x)) + 90.0
        radial = math.hypot(x, y) - self.geometry.wrist_to_tool
        vertical = z - self.geometry.base_height
        reach = math.hypot(radial, vertical)
        upper = self.geometry.shoulder_to_elbow
        lower = self.geometry.elbow_to_wrist

        min_reach = abs(upper - lower) + 1.0
        max_reach = upper + lower - 1.0
        if reach < min_reach or reach > max_reach:
            raise SecurityError(
                f"Alvo fora da cinemática segura: alcance {reach:.1f}mm "
                f"fora de {min_reach:.1f}-{max_reach:.1f}mm."
            )

        cos_elbow = (reach**2 - upper**2 - lower**2) / (2 * upper * lower)
        cos_elbow = max(-1.0, min(1.0, cos_elbow))
        elbow_internal = math.acos(cos_elbow)

        shoulder_line = math.atan2(vertical, radial)
        shoulder_offset = math.atan2(
            lower * math.sin(elbow_internal),
            upper + lower * math.cos(elbow_internal),
        )
        shoulder_rad = shoulder_line - shoulder_offset

        shoulder = 90.0 - math.degrees(shoulder_rad)
        elbow = 180.0 - math.degrees(elbow_internal)
        wrist = 90.0 + wrist_pitch - (shoulder - 90.0) - (elbow - 90.0)

        return validate_servo_angles([base, shoulder, elbow, wrist, gripper], self.limits)

    def send_angles(self, angles: Sequence[float], command: str = "MOVE") -> Dict:
        """Validate and send servo angles to the Arduino protocol."""
        if self.state.emergency_stop:
            raise SecurityError("Parada de emergencia ativa. Use clear_emergency() apos checagem humana.")

        validated = validate_servo_angles(angles, self.limits)
        line = "MOVE," + ",".join(str(int(round(angle))) for angle in validated)
        if self._serial:
            self._write_line(line)
            ack = self._serial.readline().decode("utf-8", errors="ignore").strip()
        else:
            ack = "SIMULATED"

        self.state.angles = validated
        self.state.last_command = command
        self.state.updated_at = time.time()
        return {
            "status": "success",
            "simulated": not bool(self._serial),
            "angles": validated,
            "serial_command": line,
            "ack": ack,
            "state": self.state.to_dict(),
        }

    def _write_line(self, line: str) -> None:
        if not self._serial:
            return
        self._serial.write((line.strip() + "\n").encode("utf-8"))
        self._serial.flush()


robot_controller = RobotController()
