import unittest

from chevel_main import CHEVELSystem


class SystemTests(unittest.IsolatedAsyncioTestCase):
    async def test_disallowed_program_returns_error(self):
        system = CHEVELSystem()
        response = await system.process_message("execute programa powershell")

        self.assertIn("Erro:", response)
        self.assertIn("Programa nao permitido", response)

    def test_health_shape(self):
        system = CHEVELSystem()
        health = system.health()

        self.assertEqual(health["status"], "online")
        self.assertIn("ollama", health)
        self.assertIn("native", health)


if __name__ == "__main__":
    unittest.main()

