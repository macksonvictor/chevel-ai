"""FastAPI WebSocket chat server for CHEVEL."""

from __future__ import annotations

import json
import asyncio
import html as html_lib
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from controllers.dume_controller import dume_controller
from utils.config_manager import get_config, public_model_name, resolve_model_name


WEB_ROOT = Path(__file__).resolve().parent / "web"

app = FastAPI(title="CHEVEL Chat Server")
active_connections: List[WebSocket] = []
_chevel_system = None


class AttachmentInfo(BaseModel):
    """Media/text attachment selected in the browser."""

    name: str
    size: int = 0
    type: str = ""
    kind: str = "file"
    data_url: Optional[str] = None
    text: Optional[str] = None


class ChatRequest(BaseModel):
    """HTTP chat payload used by the web interface."""

    message: str = Field(..., min_length=1)
    model: str = Field(default_factory=lambda: get_config().public_model_name)
    use_web: bool = False
    attachments: List[AttachmentInfo] = Field(default_factory=list)


class DumeCommandRequest(BaseModel):
    """Command payload for the Dum-E/U safe bridge."""

    command: str = Field(..., min_length=1)
    parameters: Dict = Field(default_factory=dict)
    confirm: bool = False
    source: str = "api"


def set_chevel_system(system) -> None:
    """Inject the running CHEVEL system instance."""
    global _chevel_system
    _chevel_system = system


def get_chevel_system():
    """Return the injected system, creating one only if needed."""
    global _chevel_system
    if _chevel_system is None:
        from chevel_main import CHEVELSystem

        _chevel_system = CHEVELSystem()
    return _chevel_system


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle one chat WebSocket connection."""
    await websocket.accept()
    active_connections.append(websocket)
    await websocket.send_json({
        "type": "system",
        "message": "CHEVEL conectado e pronto.",
        "timestamp": datetime.now().isoformat(),
    })

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = str(message_data.get("message", "")).strip()
            if not user_message:
                continue

            response = await process_with_chevel(user_message)
            await websocket.send_json({
                "type": "response",
                "message": response["text"],
                "action": response.get("action"),
                "timestamp": datetime.now().isoformat(),
            })
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def process_with_chevel(message: str) -> Dict:
    """Process a message through the CHEVEL system."""
    system = get_chevel_system()
    if hasattr(system, "process_message_detail"):
        result = await system.process_message_detail(message, route="websocket")
        return {"text": result["response"], "details": result}
    text = await system.process_message(message)
    return {"text": text}


@app.post("/api/chat")
async def chat_api(payload: ChatRequest) -> Dict:
    """Route chat messages to Ollama directly or through the web RAG path."""
    system = get_chevel_system()
    message = payload.message.strip()
    if not message:
        return {"response": "Envie uma mensagem para eu processar.", "model": payload.model}

    context: Dict = {}

    attachment_context = build_attachment_context(payload.attachments)
    if attachment_context:
        context["arquivos_anexados"] = attachment_context

    route = "ollama"
    llm_message = message
    if payload.use_web:
        route = "rag"
        context["pesquisa_web"] = await web_rag_search(message)
        llm_message = (
            "Responda usando o CONTEXTO WEB fornecido quando houver resultados. "
            "Se o contexto web estiver indisponivel, diga isso de forma curta.\n\n"
            f"Pergunta do usuario: {message}"
        )

    if hasattr(system, "process_message_detail"):
        result = await system.process_message_detail(
            message,
            context=context or None,
            model=resolve_model_name(payload.model),
            route=route,
            llm_message=llm_message,
        )
        display_model = public_model_name(payload.model)
        return {
            "response": result["response"],
            "model": display_model,
            "engine_model": result["model"],
            "route": result["route"],
            "attachments_received": attachment_context,
            "confidence": result.get("confidence"),
            "decision": result.get("decision"),
            "action": result.get("action"),
            "cognitive_health": result.get("cognitive_health"),
            "reflexes": result.get("reflexes"),
            "proactive_action": result.get("proactive_action"),
            "task_plan": result.get("task_plan"),
        }

    system.llm.model = resolve_model_name(payload.model)
    response = await asyncio.to_thread(system.llm.chat, llm_message, context or None)
    system.memory.salvar_conversa(
        message,
        str(response),
        {"rota": route, "modelo": system.llm.model, "contexto": context},
    )
    return {
        "response": response,
        "model": public_model_name(payload.model),
        "engine_model": system.llm.model,
        "route": route,
        "attachments_received": attachment_context,
    }


def build_attachment_context(attachments: List[AttachmentInfo]) -> List[Dict]:
    """Build compact attachment context without persisting raw media payloads."""
    result = []
    for item in attachments[:6]:
        entry = {
            "nome": item.name,
            "tamanho": item.size,
            "tipo": item.type,
            "categoria": item.kind,
            "recebido": bool(item.data_url or item.text),
        }
        if item.kind == "image":
            entry["observacao"] = (
                "Imagem recebida pela interface. Analise visual profunda depende de um backend multimodal HELI."
            )
        elif item.kind == "audio":
            entry["observacao"] = (
                "Audio recebido pela interface. Transcricao de arquivo de audio sera conectada ao modulo de voz/ASR."
            )
        elif item.text:
            entry["texto"] = item.text[:12000]
        result.append(entry)
    return result


async def web_rag_search(query: str) -> Dict:
    """Fetch lightweight web context for RAG without requiring an API key."""

    def fetch_instant_answer() -> Dict:
        encoded = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        })
        url = f"https://api.duckduckgo.com/?{encoded}"
        with urllib.request.urlopen(url, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_html_results() -> List[Dict[str, str]]:
        encoded = urllib.parse.urlencode({"q": query})
        request = urllib.request.Request(
            f"https://html.duckduckgo.com/html/?{encoded}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        blocks = re.findall(
            r'<a rel="nofollow" class="result__a" href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?'
            r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
            html,
            flags=re.DOTALL,
        )

        parsed = []
        for url, title, snippet in blocks[:5]:
            title_text = re.sub(r"<.*?>", "", title)
            snippet_text = re.sub(r"<.*?>", "", snippet)
            parsed.append({
                "titulo": html_lib.unescape(title_text).strip(),
                "trecho": html_lib.unescape(snippet_text).strip(),
                "url": html_lib.unescape(url).strip(),
            })
        return parsed

    try:
        data = await asyncio.to_thread(fetch_instant_answer)
    except Exception as exc:
        data = {}
        instant_error = str(exc)
    else:
        instant_error = ""

    results = []
    abstract = data.get("AbstractText")
    if abstract:
        results.append({
            "titulo": data.get("Heading") or "Resumo web",
            "trecho": abstract,
            "url": data.get("AbstractURL") or "",
        })

    for item in data.get("RelatedTopics", []):
        if "Topics" in item:
            candidates = item.get("Topics", [])
        else:
            candidates = [item]
        for topic in candidates:
            text = topic.get("Text")
            first_url = topic.get("FirstURL", "")
            if text:
                results.append({
                    "titulo": text.split(" - ", 1)[0][:120],
                    "trecho": text,
                    "url": first_url,
                })
            if len(results) >= 5:
                break
        if len(results) >= 5:
            break

    if not results:
        try:
            results = await asyncio.to_thread(fetch_html_results)
        except Exception as exc:
            return {
                "status": "indisponivel",
                "consulta": query,
                "observacao": f"Falha ao buscar contexto web: {instant_error or exc}",
                "resultados": [],
            }

    return {
        "status": "ok" if results else "sem_resultados",
        "consulta": query,
        "resultados": results,
    }


@app.get("/")
async def get_root():
    """Serve the web chat."""
    index_path = WEB_ROOT / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    """Health check for local monitoring."""
    system = get_chevel_system()
    return {
        "status": "online",
        "connections": len(active_connections),
        "system": system.health(),
    }


@app.get("/api/cognitive/health")
async def cognitive_health():
    """Return cognitive subsystem health."""
    system = get_chevel_system()
    if hasattr(system, "cognitive"):
        return system.cognitive.health()
    return {"status": "unavailable"}


@app.get("/api/cognitive/state")
async def cognitive_state():
    """Return compact cognitive state for debugging."""
    system = get_chevel_system()
    if hasattr(system, "cognitive"):
        return system.cognitive.state()
    return {"status": "unavailable"}


@app.get("/api/dume/status")
async def dume_status():
    """Return the current Dum-E/U simulated state."""
    return dume_controller.status()


@app.get("/api/dume/capabilities")
async def dume_capabilities():
    """Return Dum-E/U command and telemetry capabilities."""
    return dume_controller.capabilities()


@app.post("/api/dume/command")
async def dume_command(payload: DumeCommandRequest) -> Dict:
    """Run a Dum-E/U command through the safe simulated bridge."""
    return dume_controller.execute_command(
        payload.command,
        payload.parameters,
        confirm=payload.confirm,
        source=payload.source,
    )


@app.post("/api/dume/emergency-stop")
async def dume_emergency_stop(payload: Dict | None = None) -> Dict:
    """Trigger the Dum-E/U emergency stop path."""
    payload = payload or {}
    return dume_controller.emergency_stop(
        source=str(payload.get("source", "api")),
        reason=str(payload.get("reason", "manual")),
    )


@app.websocket("/ws/dume/telemetry")
async def dume_telemetry(websocket: WebSocket):
    """Stream Dum-E/U telemetry frames for dashboards and future ROS bridges."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(dume_controller.telemetry())
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return


app.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")
