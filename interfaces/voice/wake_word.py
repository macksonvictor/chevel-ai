"""Wake word detection for "Ola CHEVEL"."""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Callable, Optional


try:
    import pvporcupine
except Exception:  # pragma: no cover - optional runtime dependency
    pvporcupine = None

try:
    import pyaudio
except Exception:  # pragma: no cover - optional runtime dependency
    pyaudio = None

from interfaces.voice.listener import VoiceListener, VoiceListenResult


@dataclass
class WakeWordStatus:
    """Wake word runtime state."""

    active: bool
    backend: str
    message: str


@dataclass
class WakeCommandResult:
    """Combined wake-word and active command capture result."""

    wake: WakeWordStatus
    command: VoiceListenResult


class PorcupineWakeWordDetector:
    """Low-latency Porcupine wake word detector.

    A custom Picovoice keyword file for "Ola CHEVEL" can be supplied through
    CHEVEL_WAKE_WORD_PATH. Without that file, this class reports unavailable
    instead of pretending wake-word detection is active.
    """

    def __init__(self, sensitivity: float = 0.65):
        self.sensitivity = sensitivity
        self.access_key = os.getenv("PORCUPINE_ACCESS_KEY", "")
        self.keyword_path = os.getenv("CHEVEL_WAKE_WORD_PATH", "")
        self._porcupine = None
        self._pa = None
        self._stream = None

    def available(self) -> bool:
        return bool(pvporcupine and pyaudio and self.access_key and self.keyword_path)

    def listen(self, callback: Callable[[], None], max_frames: Optional[int] = None) -> WakeWordStatus:
        """Block until wake word is detected, then call callback."""
        if not self.available():
            return WakeWordStatus(False, "porcupine", "Porcupine indisponivel ou sem keyword customizada.")

        self._porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=[self.keyword_path],
            sensitivities=[self.sensitivity],
        )
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            rate=self._porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self._porcupine.frame_length,
        )

        frames = 0
        try:
            while True:
                pcm = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
                if self._porcupine.process(pcm) >= 0:
                    callback()
                    return WakeWordStatus(True, "porcupine", "Wake word detectada.")
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    return WakeWordStatus(True, "porcupine", "Limite de frames atingido.")
        finally:
            self.close()

    def listen_for_command(
        self,
        listener: VoiceListener | None = None,
        timeout: int = 5,
        phrase_time_limit: int = 10,
        max_frames: Optional[int] = None,
    ) -> WakeCommandResult:
        """Wait for wake word, then start active command listening."""
        activated = False

        def mark_active() -> None:
            nonlocal activated
            activated = True

        wake = self.listen(mark_active, max_frames=max_frames)
        if not activated or not wake.active:
            return WakeCommandResult(wake, VoiceListenResult(None, "skipped", wake.message))
        active_listener = listener or VoiceListener()
        command = active_listener.listen_command(timeout=timeout, phrase_time_limit=phrase_time_limit)
        return WakeCommandResult(wake, command)

    def close(self) -> None:
        if self._stream:
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        if self._porcupine:
            self._porcupine.delete()
        self._stream = None
        self._pa = None
        self._porcupine = None


class SimpleWakePhraseDetector:
    """Fallback detector using full speech recognition and phrase matching."""

    def __init__(
        self,
        wake_phrase: str = "ola chevel",
        language: str = "pt-BR",
        listener: VoiceListener | None = None,
    ):
        self.wake_phrase = self._normalize(wake_phrase)
        self.listener = listener or VoiceListener(language=language)

    def listen_once(self) -> WakeWordStatus:
        result = self.listener.listen_command(timeout=4, phrase_time_limit=4)
        if result.status != "ok" or not result.text:
            return WakeWordStatus(False, "speech-recognition", result.error or result.status)
        if self.wake_phrase in self._normalize(result.text):
            return WakeWordStatus(True, "speech-recognition", "Wake phrase detectada.")
        return WakeWordStatus(False, "speech-recognition", "Frase de ativacao nao encontrada.")

    def listen_for_command(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 10,
    ) -> WakeCommandResult:
        """Detect "Ola CHEVEL" and then capture the next command."""
        wake = self.listen_once()
        if not wake.active:
            return WakeCommandResult(wake, VoiceListenResult(None, "skipped", wake.message))
        command = self.listener.listen_command(timeout=timeout, phrase_time_limit=phrase_time_limit)
        return WakeCommandResult(wake, command)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = value.lower()
        replacements = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e"}
        for source, target in replacements.items():
            normalized = normalized.replace(source, target)
        return " ".join(normalized.split())


wake_word_detector = PorcupineWakeWordDetector()
