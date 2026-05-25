"""Active voice command listener for CHEVEL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional microphone dependency
    sr = None


@dataclass
class VoiceListenResult:
    """Result from a voice capture attempt."""

    text: Optional[str]
    status: str
    error: Optional[str] = None


class VoiceListener:
    """Capture one voice command after CHEVEL has been activated."""

    def __init__(self, language: str = "pt-BR", ambient_duration: float = 0.8):
        self.language = language
        self.ambient_duration = ambient_duration
        self.available = sr is not None
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = None

    def calibrate(self) -> VoiceListenResult:
        """Calibrate microphone noise level when SpeechRecognition is available."""
        if not self.available:
            return VoiceListenResult(None, "unavailable", "SpeechRecognition nao instalado.")
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=self.ambient_duration)
            return VoiceListenResult(None, "ready")
        except Exception as exc:
            return VoiceListenResult(None, "error", str(exc))

    def listen_command(self, timeout: int = 5, phrase_time_limit: int = 10) -> VoiceListenResult:
        """Listen for one command and transcribe it using the configured language."""
        if not self.available:
            return VoiceListenResult(None, "unavailable", "SpeechRecognition nao instalado.")
        if self.microphone is None:
            calibration = self.calibrate()
            if calibration.status not in {"ready", "ok"}:
                return calibration

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            text = self.recognizer.recognize_google(audio, language=self.language)
            return VoiceListenResult(text.strip(), "ok")
        except sr.WaitTimeoutError:
            return VoiceListenResult(None, "timeout", "Nenhuma fala detectada.")
        except sr.UnknownValueError:
            return VoiceListenResult(None, "unknown", "Nao entendi a fala.")
        except sr.RequestError as exc:
            return VoiceListenResult(None, "network", str(exc))
        except Exception as exc:
            return VoiceListenResult(None, "error", str(exc))


voice_listener = VoiceListener()
