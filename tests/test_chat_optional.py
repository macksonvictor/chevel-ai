import unittest


try:
    from fastapi.testclient import TestClient

    from chevel_main import CHEVELSystem
    from interfaces.chat.server import app, set_chevel_system
except Exception as exc:  # pragma: no cover - optional dependency
    TestClient = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TestClient is None, f"FastAPI test client unavailable: {IMPORT_ERROR}")
class ChatTests(unittest.TestCase):
    def test_health_endpoint(self):
        set_chevel_system(CHEVELSystem())
        client = TestClient(app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    def test_websocket_round_trip(self):
        set_chevel_system(CHEVELSystem())
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            system_message = websocket.receive_json()
            self.assertEqual(system_message["type"], "system")

            websocket.send_json({"message": "execute programa powershell"})
            response = websocket.receive_json()

        self.assertEqual(response["type"], "response")
        self.assertIn("Programa nao permitido", response["message"])

    def test_api_chat_routes_to_requested_model(self):
        class FakeLLM:
            def __init__(self):
                self.model = "unset"
                self.calls = []

            def chat(self, message, context=None):
                self.calls.append((message, context))
                return "OK fake"

        class FakeMemory:
            def __init__(self):
                self.saved = []

            def salvar_conversa(self, user, assistant, context=None):
                self.saved.append((user, assistant, context))

        class FakeSystem:
            def __init__(self):
                self.llm = FakeLLM()
                self.memory = FakeMemory()

        fake = FakeSystem()
        set_chevel_system(fake)
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message": "ola",
            "model": "llama3.2:latest",
            "use_web": False,
            "attachments": [{"name": "a.txt", "size": 12, "type": "text/plain"}],
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["response"], "OK fake")
        self.assertEqual(data["model"], "HELI 1.5")
        self.assertEqual(data["engine_model"], "llama3.2:latest")
        self.assertEqual(data["route"], "ollama")
        self.assertEqual(fake.llm.model, "llama3.2:latest")
        self.assertEqual(fake.llm.calls[0][0], "ola")
        self.assertEqual(
            fake.llm.calls[0][1]["arquivos_anexados"][0]["nome"],
            "a.txt",
        )

    def test_cognitive_endpoints(self):
        set_chevel_system(CHEVELSystem())
        client = TestClient(app)

        health = client.get("/api/cognitive/health")
        state = client.get("/api/cognitive/state")

        self.assertEqual(health.status_code, 200)
        self.assertIn("self_monitor", health.json())
        self.assertEqual(state.status_code, 200)
        self.assertIn("world_model", state.json())


if __name__ == "__main__":
    unittest.main()
