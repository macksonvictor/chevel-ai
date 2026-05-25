"""Intent processor for CHEVEL commands."""

from __future__ import annotations

import json
import re
import asyncio
from typing import Dict, Optional, Tuple

from core.llm_engine import chevel_llm
from utils.native_bridge import detect_intent


class CHEVELIntentProcessor:
    """Detect quick actions and ask the LLM for free-form messages."""

    def __init__(self):
        self.action_patterns = self._load_action_patterns()

    def _load_action_patterns(self) -> Dict[str, list[str]]:
        return {
            "dume_emergency_stop": [
                r"\b(?:parada\s+de\s+emergencia|emergencia|pare\s+tudo|parar\s+tudo|pare\s+o\s+dum-?e|stop\s+dum-?e)\b",
            ],
            "dume_command": [
                r"\b(?:mande|mova|mover|leve|volte|retorne|posicione)\b.+\b(?:dum-?e|braco|braço|robo|robô)\b.+\bhome\b",
                r"\b(?:abra|abrir|feche|fechar)\b.+\bgarra\b",
                r"\b(?:pegue|pegar|traga|trazer|entregue|entregar)\b.+",
                r"\b(?:navegue|navegar|va|vá)\b.+\b(?:bancada|porta|base|mesa|usuario|usuário|workbench)\b",
            ],
            "buscar_arquivo": [
                r"\b(?:busque|buscar|procure|procurar|encontre|encontrar)\s+(?:o\s+)?(?:arquivo|pasta|documento)\s+(.+)$",
                r"\b(?:busque|buscar|procure|procurar|encontre|encontrar)\s+(.+)$",
            ],
            "abrir_arquivo": [
                r"\b(?:abra|abrir|abre|acesse|acessar)\s+(?:o\s+)?(?:arquivo|documento|pasta)\s+(.+)$",
            ],
            "executar_programa": [
                r"\b(?:abra|abrir|abre|execute|executar|executa|rode|rodar)\s+(?:o\s+)?(?:programa|app|aplicativo)\s+(.+)$",
                r"\b(?:abra|abrir|abre)\s+(.+)$",
            ],
            "enviar_email": [
                r"\b(?:enviar|envie|mandar|mande)\s+(?:um\s+)?email\s+para\s+(.+)$",
            ],
            "controlar_luz": [
                r"\b(acenda|apague|ligue|desligue|acender|apagar|ligar|desligar)\s+(?:a\s+)?luz(?:\s+d[ao]\s+(.+))?$",
            ],
            "mover_braco": [
                r"\b(?:mova|mover|posicione|posicionar)\s+(?:o\s+)?braco(?:\s+(.+))?$",
            ],
        }

    async def processar(
        self,
        mensagem: str,
        contexto: Dict | None = None,
        llm_message: str | None = None,
    ) -> Tuple[str, Optional[Dict]]:
        """Return a response text and optional action dictionary."""
        acao_rapida = self._detectar_acao_rapida(mensagem)
        if acao_rapida:
            return await self._processar_acao(acao_rapida)

        resposta_llm = await asyncio.to_thread(chevel_llm.chat, llm_message or mensagem, contexto)
        if not isinstance(resposta_llm, str):
            resposta_llm = "".join(resposta_llm)

        acao_llm = self._extrair_acao_de_resposta(resposta_llm)
        if acao_llm:
            return (acao_llm.get("mensagem", "Executando acao."), acao_llm)
        return (resposta_llm, None)

    def _detectar_acao_rapida(self, mensagem: str) -> Optional[Dict]:
        native_action = detect_intent(mensagem)
        if native_action:
            native_action.pop("matched", None)
            return native_action

        for tipo_acao, padroes in self.action_patterns.items():
            for padrao in padroes:
                match = re.search(padrao, mensagem.strip(), re.IGNORECASE)
                if match:
                    return {
                        "tipo": "acao",
                        "acao": tipo_acao,
                        "parametros": self._extrair_parametros(match, tipo_acao),
                        "confianca": 0.9,
                    }
        return None

    def _extrair_parametros(self, match: re.Match, tipo_acao: str) -> Dict:
        parametros: Dict[str, str] = {}
        if tipo_acao == "abrir_arquivo":
            parametros["caminho"] = match.group(1).strip()
        elif tipo_acao == "buscar_arquivo":
            parametros["nome"] = match.group(1).strip()
        elif tipo_acao == "executar_programa":
            parametros["programa"] = match.group(1).strip()
        elif tipo_acao == "enviar_email":
            parametros["destinatario"] = match.group(1).strip()
        elif tipo_acao == "controlar_luz":
            verbo = match.group(1).lower()
            parametros["acao"] = "on" if verbo.startswith(("acend", "lig")) else "off"
            if match.lastindex and match.lastindex >= 2 and match.group(2):
                parametros["local"] = match.group(2).strip()
        elif tipo_acao == "mover_braco":
            if match.lastindex and match.group(1):
                parametros["instrucao"] = match.group(1).strip()
        elif tipo_acao == "dume_emergency_stop":
            parametros["reason"] = match.group(0).strip()
        elif tipo_acao == "dume_command":
            instruction = match.group(0).strip()
            lower = instruction.lower()
            if "home" in lower:
                command = "home"
            elif "garra" in lower and lower.startswith(("abra", "abrir")):
                command = "open_gripper"
            elif "garra" in lower and lower.startswith(("feche", "fechar")):
                command = "close_gripper"
            elif lower.startswith(("pegue", "pegar", "traga", "trazer")):
                command = "pick"
            elif lower.startswith(("entregue", "entregar")):
                command = "deliver"
            elif lower.startswith(("navegue", "navegar", "va", "vá")):
                command = "navigate"
            else:
                command = "move_arm"
            parametros["command"] = command
            parametros["parameters"] = {"instruction": instruction}
        return parametros

    def _extrair_acao_de_resposta(self, resposta: str) -> Optional[Dict]:
        json_match = re.search(r"```json\s*(\{.+?\})\s*```", resposta, re.DOTALL)
        candidates = []
        if json_match:
            candidates.append(json_match.group(1))

        inicio = resposta.find("{")
        fim = resposta.rfind("}") + 1
        if inicio != -1 and fim > inicio:
            candidates.append(resposta[inicio:fim])

        for candidate in candidates:
            try:
                acao = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if acao.get("tipo") == "acao" and acao.get("acao"):
                acao.setdefault("parametros", {})
                return acao
        return None

    async def _processar_acao(self, acao: Dict) -> Tuple[str, Dict]:
        tipo = acao["acao"]
        params = acao.get("parametros", {})
        mensagens = {
            "abrir_arquivo": f"Abrindo arquivo: {params.get('caminho')}",
            "buscar_arquivo": f"Buscando arquivo: {params.get('nome')}",
            "executar_programa": f"Executando programa: {params.get('programa')}",
            "enviar_email": f"Preparando email para: {params.get('destinatario')}",
            "controlar_luz": "Controlando luz via stub IoT.",
            "mover_braco": "Movendo braco robotico via stub.",
            "dume_command": f"Preparando comando Dum-E/U: {params.get('command')}",
            "dume_emergency_stop": "Acionando parada de emergencia Dum-E/U.",
        }
        return (mensagens.get(tipo, "Executando acao."), acao)


chevel_intent = CHEVELIntentProcessor()
