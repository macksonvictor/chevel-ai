import unittest

from controllers.dume_controller import DumeController


try:
    from fastapi.testclient import TestClient

    from interfaces.chat.server import app
except Exception as exc:  # pragma: no cover - optional dependency
    TestClient = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class DumeControllerTests(unittest.TestCase):
    def test_motion_command_requires_confirmation(self):
        controller = DumeController()
        result = controller.execute_command("home")

        self.assertEqual(result["status"], "requires_confirmation")
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["risk"], "medio")

    def test_confirmed_motion_is_simulated(self):
        controller = DumeController()
        result = controller.execute_command("home", confirm=True)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["simulated"])
        self.assertEqual(result["state"]["joints"], [0.0] * 7)

    def test_emergency_stop_is_always_allowed(self):
        controller = DumeController()
        result = controller.execute_command("emergency_stop")

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["state"]["emergency_stop"])
        self.assertEqual(result["risk"], "seguro")


@unittest.skipIf(TestClient is None, f"FastAPI test client unavailable: {IMPORT_ERROR}")
class DumeApiTests(unittest.TestCase):
    def test_dume_status_and_capabilities_endpoints(self):
        client = TestClient(app)

        status = client.get("/api/dume/status")
        capabilities = client.get("/api/dume/capabilities")

        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["platform"], "Dum-E/U")
        self.assertEqual(capabilities.status_code, 200)
        self.assertIn("home", capabilities.json()["commands"])

    def test_dume_command_blocks_motion_without_confirmation(self):
        client = TestClient(app)

        response = client.post("/api/dume/command", json={"command": "home"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "requires_confirmation")

    def test_dume_emergency_endpoint(self):
        client = TestClient(app)

        response = client.post("/api/dume/emergency-stop", json={"reason": "test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertTrue(response.json()["state"]["emergency_stop"])


if __name__ == "__main__":
    unittest.main()
