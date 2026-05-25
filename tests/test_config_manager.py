import json
import tempfile
import unittest
from pathlib import Path

from utils.config_manager import load_config


class ConfigManagerTests(unittest.TestCase):
    def test_defaults_load_without_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(config_dir=tmp, env={})

        self.assertEqual(config.public_model_name, "HELI 1.5")
        self.assertEqual(config.ollama_model, "llama3.1:8b")
        self.assertTrue(config.memory_db_path.name.endswith("chevel.db"))
        self.assertTrue(config.robot_arm_simulate)

    def test_local_json_files_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            (config_dir / "chevel.local.json").write_text(
                json.dumps({
                    "core": {
                        "ollama_model": "llama3.1:70b",
                        "max_history": 7,
                    },
                    "paths": {
                        "user_profile_path": "data/memory/custom-profile.local.json"
                    },
                    "actions": {
                        "allowed_programs": {
                            "code": "code.exe"
                        }
                    }
                }),
                encoding="utf-8",
            )
            (config_dir / "voice.local.json").write_text(
                json.dumps({
                    "voice": {
                        "enabled": True,
                        "backend": "speech-recognition",
                        "wake_phrase": "ola chevel"
                    }
                }),
                encoding="utf-8",
            )

            config = load_config(config_dir=config_dir, env={})

        self.assertEqual(config.ollama_model, "llama3.1:70b")
        self.assertEqual(config.max_history, 7)
        self.assertEqual(config.allowed_programs["code"], ["code.exe"])
        self.assertTrue(
            config.user_profile_path.as_posix().endswith("data/memory/custom-profile.local.json")
        )
        self.assertTrue(config.voice_enabled)
        self.assertEqual(config.voice_backend, "speech-recognition")

    def test_environment_overrides_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            (config_dir / "chevel.local.json").write_text(
                json.dumps({
                    "core": {
                        "ollama_model": "llama3.1:70b",
                        "public_model_name": "LOCAL NAME",
                        "max_history": 4
                    }
                }),
                encoding="utf-8",
            )

            config = load_config(
                config_dir=config_dir,
                env={
                    "CHEVEL_MODEL": "llama3.1:8b",
                    "CHEVEL_PUBLIC_MODEL": "HELI TEST",
                    "CHEVEL_MAX_HISTORY": "11",
                    "CHEVEL_USER_PROFILE_PATH": "data/memory/env-profile.local.json",
                },
            )

        self.assertEqual(config.ollama_model, "llama3.1:8b")
        self.assertEqual(config.public_model_name, "HELI TEST")
        self.assertEqual(config.max_history, 11)
        self.assertTrue(
            config.user_profile_path.as_posix().endswith("data/memory/env-profile.local.json")
        )

    def test_dotenv_values_are_loaded_when_env_not_injected(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join([
                    "CHEVEL_MODEL=llama3.1:70b",
                    "CHEVEL_PUBLIC_MODEL=HELI DOTENV",
                    "CHEVEL_MAX_HISTORY=9",
                ]),
                encoding="utf-8",
            )

            config = load_config(
                config_dir=Path(tmp) / "configs",
                env_file=env_path,
            )

        self.assertEqual(config.ollama_model, "llama3.1:70b")
        self.assertEqual(config.public_model_name, "HELI DOTENV")
        self.assertEqual(config.max_history, 9)

    def test_missing_explicit_private_config_is_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(
                config_dir=tmp,
                config_path=Path(tmp) / "does-not-exist.local.json",
                env={},
            )

        self.assertEqual(config.dume_mode, "simulation")


if __name__ == "__main__":
    unittest.main()
