import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicScopeFilesTests(unittest.TestCase):
    def test_required_public_scope_files_exist(self):
        required = [
            "docs/CONFIGURATION.md",
            "docs/UNIVERSAL_SCOPE.md",
            "docs/releases/v0.2.0.md",
            "data/configs/README.md",
            "data/configs/chevel.example.json",
            "data/configs/voice.example.json",
            "data/configs/dume.example.json",
            "data/configs/robot-arm.example.json",
            "data/configs/integrations.example.json",
            "data/configs/safety.example.json",
            "data/models/README.md",
            "data/models/model-manifest.example.json",
            "data/workflows/README.md",
            "data/workflows/workflow-manifest.example.json",
        ]

        missing = [item for item in required if not (ROOT / item).is_file()]
        self.assertEqual(missing, [])

    def test_public_json_examples_are_valid(self):
        examples = list((ROOT / "data" / "configs").glob("*.example.json"))
        examples += list((ROOT / "data" / "models").glob("*.example.json"))
        examples += list((ROOT / "data" / "workflows").glob("*.example.json"))

        self.assertGreaterEqual(len(examples), 8)
        for path in examples:
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)

    def test_readme_points_to_new_scope_docs(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Capability Matrix", readme)
        self.assertIn("./docs/CONFIGURATION.md", readme)
        self.assertIn("./docs/UNIVERSAL_SCOPE.md", readme)
        self.assertIn("v0.2.0", readme)


if __name__ == "__main__":
    unittest.main()
