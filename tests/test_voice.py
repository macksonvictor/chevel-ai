import unittest

from interfaces.voice.listener import VoiceListener
from interfaces.voice.wake_word import SimpleWakePhraseDetector


class VoiceModuleTests(unittest.TestCase):
    def test_listener_reports_availability_shape(self):
        listener = VoiceListener()

        self.assertIsInstance(listener.available, bool)

    def test_wake_phrase_normalization(self):
        detector = SimpleWakePhraseDetector()

        self.assertIn("ola chevel", detector._normalize("Olá   CHEVEL"))


if __name__ == "__main__":
    unittest.main()
