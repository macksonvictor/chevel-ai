import tempfile
import unittest
from pathlib import Path

from controllers.os_controller import OSController
from utils.security import (
    SecurityError,
    ensure_existing_path,
    get_allowed_program_command,
    servo_limits_manifest,
    validate_cartesian_workspace,
    validate_servo_angles,
    validate_servo_payload,
)


class SecurityTests(unittest.TestCase):
    def test_allowed_program(self):
        self.assertEqual(get_allowed_program_command("calc"), ["calc.exe"])

    def test_shell_command_blocked(self):
        with self.assertRaises(SecurityError):
            get_allowed_program_command("cmd /c dir & whoami")

    def test_unknown_program_blocked_by_controller(self):
        result = OSController().executar_programa("powershell")
        self.assertEqual(result["status"], "error")
        self.assertIn("nao permitido", result["mensagem"])

    def test_existing_path_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.txt"
            path.write_text("ok", encoding="utf-8")
            self.assertEqual(ensure_existing_path(str(path)), path.resolve())

    def test_servo_angle_validation(self):
        self.assertEqual(validate_servo_angles([90, 90, 90, 90, 90]), [90, 90, 90, 90, 90])
        with self.assertRaises(SecurityError):
            validate_servo_angles([90, 0, 90, 90, 90])

    def test_servo_payload_validation(self):
        payload = {
            "base": 90,
            "shoulder": 90,
            "elbow": 90,
            "wrist": 90,
            "gripper": 90,
        }

        self.assertEqual(validate_servo_payload(payload), [90, 90, 90, 90, 90])
        self.assertEqual(servo_limits_manifest()[0]["name"], "base")
        with self.assertRaises(SecurityError):
            validate_servo_payload({"base": 90})

    def test_cartesian_workspace_validation(self):
        validate_cartesian_workspace(120, 0, 80)
        with self.assertRaises(SecurityError):
            validate_cartesian_workspace(500, 0, 80)


if __name__ == "__main__":
    unittest.main()
