import tempfile
import unittest
from pathlib import Path

from controllers.os_controller import OSController
from utils.security import (
    SecurityError,
    ensure_existing_path,
    get_allowed_program_command,
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


if __name__ == "__main__":
    unittest.main()

