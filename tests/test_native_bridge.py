import unittest

from utils.native_bridge import (
    assess_action_risk,
    cosine_similarity_batch,
    evaluate_reflexes,
    native_version,
)


class NativeBridgeTests(unittest.TestCase):
    def test_fallback_similarity(self):
        scores = cosine_similarity_batch([1.0, 0.0], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])

        self.assertAlmostEqual(scores[0], 1.0)
        self.assertAlmostEqual(scores[1], 0.0)
        self.assertAlmostEqual(scores[2], 0.0)

    def test_version_string(self):
        self.assertIsInstance(native_version(), str)

    def test_action_risk_bridge(self):
        risk = assess_action_risk("executar_programa", {"programa": "calc"})

        self.assertIsNotNone(risk)
        self.assertEqual(risk["risk"], "baixo")

    def test_reflex_bridge(self):
        reflexes = evaluate_reflexes({"bateria": 8})

        self.assertIsInstance(reflexes, list)
        self.assertTrue(any(item["acao"]["tipo"] == "parada_emergencia" for item in reflexes))


if __name__ == "__main__":
    unittest.main()
