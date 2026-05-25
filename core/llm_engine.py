"""Local Ollama-backed LLM engine for CHEVEL."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from typing import Dict, Generator, Iterable, List, Optional

from core.personality import build_system_prompt
from utils.config_manager import get_config


class CHEVELLLMEngine:
    """Small Ollama client with offline-safe behavior."""

    def __init__(self, model: str | None = None, host: str | None = None):
        config = get_config()
        self.model = model or config.ollama_model
        self.host = (host or config.ollama_host).rstrip("/")
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = config.max_history
        self._server_started_by_chevel = False

    def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        stream: bool = False,
    ) -> str | Iterable[str]:
        """Chat with the configured local Ollama model."""
        self._ensure_server_available()
        messages = self._build_messages(message, context)

        if stream:
            return self._chat_stream(messages, message)

        selected_model = self._select_model()
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
        }

        try:
            data = self._post_json("/api/chat", payload)
        except urllib.error.URLError:
            return self._offline_message()
        except TimeoutError:
            return self._offline_message()
        except Exception as exc:
            return f"Erro ao processar no Ollama: {exc}"

        assistant_message = data.get("message", {}).get("content", "")
        if not assistant_message:
            assistant_message = "Ollama respondeu sem conteudo."
        self._save_to_history(message, assistant_message)
        return assistant_message

    def health(self) -> Dict[str, object]:
        """Return Ollama health and model visibility."""
        self._ensure_server_available()
        try:
            tags = self._get_json("/api/tags")
        except Exception as exc:
            return {
                "online": False,
                "model": self.model,
                "message": f"Ollama offline ou inacessivel: {exc}",
            }

        models = [item.get("name") for item in tags.get("models", [])]
        return {
            "online": True,
            "configured_model": self.model,
            "active_model": self._select_model(models),
            "model_available": self.model in models,
            "models": models,
        }

    def clear_history(self) -> None:
        """Clear in-memory conversation context."""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Return the in-memory conversation context."""
        return list(self.conversation_history)

    def _build_messages(self, message: str, context: Optional[Dict]) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": build_system_prompt()}]
        messages.extend(self.conversation_history[-self.max_history * 2 :])

        if context:
            messages.append({
                "role": "system",
                "content": "CONTEXTO ADICIONAL:\n" + self._format_context(context),
            })

        messages.append({"role": "user", "content": message})
        return messages

    def _chat_stream(
        self, messages: List[Dict[str, str]], user_message: str
    ) -> Generator[str, None, None]:
        payload = {"model": self._select_model(), "messages": messages, "stream": True}
        full_response = ""
        try:
            request = self._request("/api/chat", payload)
            with urllib.request.urlopen(request, timeout=60) as response:
                for line in response:
                    if not line:
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_response += content
                        yield content
        except Exception:
            fallback = self._offline_message()
            full_response = fallback
            yield fallback
        finally:
            if full_response:
                self._save_to_history(user_message, full_response)

    def _format_context(self, context: Dict) -> str:
        parts = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                formatted = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                formatted = str(value)
            parts.append(f"{key}:\n{formatted}")
        return "\n\n".join(parts)

    def _save_to_history(self, user_msg: str, assistant_msg: str) -> None:
        self.conversation_history.append({"role": "user", "content": user_msg})
        self.conversation_history.append({"role": "assistant", "content": assistant_msg})
        limit = self.max_history * 2
        if len(self.conversation_history) > limit:
            self.conversation_history = self.conversation_history[-limit:]

    def _offline_message(self) -> str:
        return (
            "chevel local esta online, mas o Ollama nao esta respondendo. "
            "Inicie o Ollama Desktop ou rode 'ollama serve' e tente novamente."
        )

    def _ensure_server_available(self) -> None:
        """Start `ollama serve` in the background when the local API is down."""
        try:
            self._get_json("/api/tags", start_if_down=False)
            return
        except Exception:
            pass

        if self._server_started_by_chevel:
            return

        ollama_exe = shutil.which("ollama")
        if not ollama_exe:
            return

        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            subprocess.Popen(
                [ollama_exe, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self._server_started_by_chevel = True
        except Exception:
            return

        for _ in range(10):
            time.sleep(0.5)
            try:
                self._get_json("/api/tags", start_if_down=False)
                return
            except Exception:
                continue

    def _select_model(self, models: Optional[List[str]] = None) -> str:
        """Use the configured model, or the first installed model as a local fallback."""
        if models is None:
            try:
                tags = self._get_json("/api/tags")
                models = [item.get("name") for item in tags.get("models", [])]
            except Exception:
                return self.model

        if self.model in models:
            return self.model
        if models:
            return models[0]
        return self.model

    def _request(self, path: str, payload: Dict) -> urllib.request.Request:
        body = json.dumps(payload).encode("utf-8")
        return urllib.request.Request(
            self.host + path,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    def _post_json(self, path: str, payload: Dict) -> Dict:
        request = self._request(path, payload)
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_json(self, path: str, start_if_down: bool = True) -> Dict:
        if start_if_down:
            self._ensure_server_available()
        with urllib.request.urlopen(self.host + path, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


chevel_llm = CHEVELLLMEngine()
