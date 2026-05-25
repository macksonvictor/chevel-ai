import unittest

from core.intent_processor import CHEVELIntentProcessor


class IntentTests(unittest.IsolatedAsyncioTestCase):
    async def test_program_action(self):
        processor = CHEVELIntentProcessor()
        response, action = await processor.processar("abra calculadora")

        self.assertIn("Executando programa", response)
        self.assertEqual(action["acao"], "executar_programa")
        self.assertEqual(action["parametros"]["programa"].lower(), "calculadora")

    async def test_file_action(self):
        processor = CHEVELIntentProcessor()
        _, action = await processor.processar("abrir arquivo C:\\temp\\teste.txt")

        self.assertEqual(action["acao"], "abrir_arquivo")
        self.assertEqual(action["parametros"]["caminho"], "C:\\temp\\teste.txt")

    async def test_light_action(self):
        processor = CHEVELIntentProcessor()
        _, action = await processor.processar("apague a luz da sala")

        self.assertEqual(action["acao"], "controlar_luz")
        self.assertEqual(action["parametros"]["acao"], "off")
        self.assertEqual(action["parametros"]["local"], "sala")


if __name__ == "__main__":
    unittest.main()

