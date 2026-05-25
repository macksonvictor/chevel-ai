import unittest

from interfaces.voice.listener import VoiceListener
from interfaces.voice.listener import VoiceListenResult
from interfaces.voice.wake_word import SimpleWakePhraseDetector


class FakeListener:
    def __init__(self, results):
        self.results = list(results)

    def listen_command(self, timeout=5, phrase_time_limit=10):
        return self.results.pop(0)


class VoiceModuleTests(unittest.TestCase):
    def test_listener_reports_availability_shape(self):
        listener = VoiceListener()

        self.assertIsInstance(listener.available, bool)

    def test_wake_phrase_normalization(self):
        detector = SimpleWakePhraseDetector()

        self.assertIn("ola chevel", detector._normalize("Olá   CHEVEL"))

    def test_wake_phrase_starts_active_command_listening(self):
        detector = SimpleWakePhraseDetector(
            listener=FakeListener([
                VoiceListenResult("Olá CHEVEL", "ok"),
                VoiceListenResult("mova para home", "ok"),
            ])
        )

        result = detector.listen_for_command()

        self.assertTrue(result.wake.active)
        self.assertEqual(result.command.text, "mova para home")


if __name__ == "__main__":
    unittest.main()
