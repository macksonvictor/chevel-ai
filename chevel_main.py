"""CHEVEL AI MVP entry point."""

from __future__ import annotations

import argparse
import asyncio
from typing import Dict, Optional

from controllers.comm_controller import communication_controller
from controllers.dume_controller import dume_controller
from controllers.iot_controller import iot_controller
from controllers.os_controller import os_controller
from controllers.robot_controller import robot_controller
from core.cognitive_core import cognitive_core
from core.intent_processor import chevel_intent
from core.llm_engine import chevel_llm
from core.memory_system import chevel_memory
from utils.logger import setup_logger
from utils.native_bridge import native_available, native_version


class CHEVELSystem:
    """Coordinates memory, intent processing, LLM responses, and actions."""

    def __init__(self):
        self.log = setup_logger("chevel")
        self.llm = chevel_llm
        self.memory = chevel_memory
        self.intent = chevel_intent
        self.cognitive = cognitive_core
        self.os = os_controller
        self.iot = iot_controller
        self.comm = communication_controller
        self.robot = robot_controller
        self.dume = dume_controller
        self.cognitive.start_background_loops()

    async def process_message(self, message: str) -> str:
        """Process one user message end to end."""
        result = await self.process_message_detail(message)
        return result["response"]

    async def process_message_detail(
        self,
        message: str,
        *,
        context: Optional[Dict] = None,
        model: str | None = None,
        route: str = "cognitive",
        llm_message: str | None = None,
        sensor_data: Optional[Dict] = None,
    ) -> Dict:
        """Process one user message and return the full cognitive payload."""
        if model:
            self.llm.model = model

        result = await self.cognitive.processar(
            message,
            llm=self.llm,
            memory=self.memory,
            intent=self.intent,
            executor=self._executar_acao,
            dados_sensores=sensor_data,
            contexto_extra=context,
            mensagem_llm=llm_message,
            route=route,
        )
        if result.action and result.action.get("type"):
            self.log.info("Cognitive action: %s", result.action.get("type"))
        return result.to_dict()

    def health(self) -> Dict:
        """Return local runtime health."""
        return {
            "status": "online",
            "ollama": self.llm.health(),
            "native": {
                "available": native_available(),
                "version": native_version(),
            },
            "cognitive": self.cognitive.health(),
            "dume": self.dume.summary(),
        }

    async def _executar_acao(self, acao: Dict) -> Dict:
        tipo = acao.get("acao")
        params = acao.get("parametros", {})

        if tipo == "abrir_arquivo":
            return self.os.abrir_arquivo(params.get("caminho", ""))
        if tipo == "executar_programa":
            return self.os.executar_programa(params.get("programa", ""))
        if tipo == "buscar_arquivo":
            resultados = self.os.buscar_arquivos(params.get("nome", ""))
            return {
                "status": "success",
                "mensagem": f"Encontrados {len(resultados)} resultado(s).",
                "resultados": resultados,
            }
        if tipo == "controlar_luz":
            entidade = params.get("entidade") or params.get("local") or "light.sala"
            return self.iot.controlar_luz(entidade, params.get("acao", "toggle"))
        if tipo == "enviar_email":
            return self.comm.enviar_email(params.get("destinatario", ""))
        if tipo == "mover_braco":
            command = params.get("command") or params.get("comando") or "move_arm"
            return self.dume.execute_command(
                command,
                params,
                confirm=bool(params.get("confirm") or params.get("confirmado")),
                source="cognitive",
            )
        if tipo == "dume_command":
            return self.dume.execute_command(
                params.get("command", "status"),
                params.get("parameters", params),
                confirm=bool(params.get("confirm") or params.get("confirmado")),
                source="cognitive",
            )
        if tipo == "dume_emergency_stop":
            return self.dume.emergency_stop(source="cognitive", reason=params.get("reason", "voice"))

        return {
            "status": "error",
            "mensagem": f"Acao nao implementada: {tipo}",
        }

    def _append_action_result(self, resposta: str, resultado: Dict) -> str:
        status = resultado.get("status")
        mensagem = resultado.get("mensagem", "")
        if status == "success":
            return f"{resposta}\nOK: {mensagem}"
        if status in {"stub", "needs_input"}:
            return f"{resposta}\nInfo: {mensagem}"
        return f"{resposta}\nErro: {mensagem}"

    def start_chat_server(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the FastAPI chat server."""
        try:
            import uvicorn
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Instale as dependencias do chat com: pip install -r requirements.txt"
            ) from exc

        from interfaces.chat.server import app, set_chevel_system

        set_chevel_system(self)
        print(f"CHEVEL chat online em http://localhost:{port}")
        uvicorn.run(app, host=host, port=port)

    async def interactive_mode(self) -> None:
        """Run the CLI loop."""
        print("CHEVEL AI CLI ativo. Digite 'sair' para encerrar.")
        print(f"Modulo nativo: {native_version()}")
        while True:
            try:
                user_input = input("Voce: ").strip()
                if user_input.lower() in {"sair", "exit", "quit"}:
                    print("Ate logo.")
                    return
                resposta = await self.process_message(user_input)
                print(f"CHEVEL: {resposta}")
            except KeyboardInterrupt:
                print("\nEncerrando.")
                return
            except Exception as exc:
                print(f"Erro: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CHEVEL AI MVP")
    parser.add_argument(
        "--mode",
        choices=["cli", "chat"],
        default="cli",
        help="Interface mode.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Chat server host.")
    parser.add_argument("--port", default=8000, type=int, help="Chat server port.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    chevel = CHEVELSystem()
    if args.mode == "chat":
        chevel.start_chat_server(args.host, args.port)
    else:
        asyncio.run(chevel.interactive_mode())


if __name__ == "__main__":
    main()
