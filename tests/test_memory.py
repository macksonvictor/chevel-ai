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
            json_rows = memory.recuperar_interacoes_json(1)
            self.assertEqual(json_rows[0]["usuario"], "ola")
            self.assertEqual(json_rows[0]["chevel"], "CHEVEL online")
            memory.close()

    def test_save_and_fetch_json_interaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = CHEVELMemory(Path(tmp) / "memory.db")
            path = memory.salvar_interacao_json(
                "abrir calculadora",
                "Executando calculadora",
                {"source": "json-test"},
            )
            rows = memory.recuperar_interacoes_json(5)

            self.assertTrue(path.exists())
            self.assertEqual(rows[0]["usuario"], "abrir calculadora")
            self.assertEqual(rows[0]["contexto"]["source"], "json-test")
            memory.close()

    def test_knowledge_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = CHEVELMemory(Path(tmp) / "memory.db")
            memory.salvar_conhecimento("perfil", "chevel", "projeto local")
            context = memory.gerar_contexto_para_llm("o que e chevel?")

            self.assertIn("conhecimento", context)
            self.assertEqual(context["conhecimento"][0]["valor"], "projeto local")
            memory.close()

    def test_private_user_profile_is_loaded_into_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "profile.local.json"
            profile_path.write_text(
                """
                {
                  "schema": "chevel.user_profile.v1",
                  "profile": {
                    "preferred_name": "Mackson",
                    "language": "pt-BR"
                  },
                  "communication_style": ["direto", "honesto"]
                }
                """,
                encoding="utf-8",
            )
            memory = CHEVELMemory(Path(tmp) / "memory.db", profile_path=profile_path)
            context = memory.gerar_contexto_para_llm("o que sabe sobre mim?")

            self.assertEqual(context["perfil_usuario"]["profile"]["preferred_name"], "Mackson")
            self.assertEqual(context["perfil_usuario"]["communication_style"], ["direto", "honesto"])
            memory.close()

    def test_private_user_profile_strips_secret_like_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "profile.local.json"
            profile_path.write_text(
                """
                {
                  "profile": {"preferred_name": "Mackson"},
                  "secrets": {"token": "nao-deve-aparecer"},
                  "nested": {"password": "nao-deve-aparecer", "safe": "ok"}
                }
                """,
                encoding="utf-8",
            )
            memory = CHEVELMemory(Path(tmp) / "memory.db", profile_path=profile_path)
            context = memory.gerar_contexto_para_llm("perfil")

            serialized = str(context["perfil_usuario"])
            self.assertIn("Mackson", serialized)
            self.assertIn("ok", serialized)
            self.assertNotIn("nao-deve-aparecer", serialized)
            memory.close()


if __name__ == "__main__":
    unittest.main()
