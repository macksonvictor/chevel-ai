import tempfile
import unittest
from pathlib import Path

from core.memory_system import CHEVELMemory


class MemoryTests(unittest.TestCase):
    def test_save_and_fetch_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = CHEVELMemory(Path(tmp) / "memory.db")
            conversation_id = memory.salvar_conversa(
                "ola",
                "CHEVEL online",
                {"source": "test"},
            )
            rows = memory.buscar_conversas_recentes(1)

            self.assertGreater(conversation_id, 0)
            self.assertEqual(rows[0]["usuario"], "ola")
            self.assertEqual(rows[0]["chevel"], "CHEVEL online")
            memory.close()

    def test_knowledge_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = CHEVELMemory(Path(tmp) / "memory.db")
            memory.salvar_conhecimento("perfil", "chevel", "projeto local")
            context = memory.gerar_contexto_para_llm("o que e chevel?")

            self.assertIn("conhecimento", context)
            self.assertEqual(context["conhecimento"][0]["valor"], "projeto local")
            memory.close()


if __name__ == "__main__":
    unittest.main()

