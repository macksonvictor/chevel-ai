"""Unified cognitive processing pipeline for CHEVEL."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, Dict, Optional

from core.decision_engine import decision_engine
from core.fast_thinking import fast_thinking
from core.goal_system import goal_system
from core.learning_system import Episodio, behavior_optimizer, experience_buffer
from core.self_monitor import self_monitor
from core.task_reasoning import task_engine
from core.world_model import world_model


ActionExecutor = Callable[[Dict], Awaitable[Dict] | Dict]


@dataclass
class ResultadoCognitivo:
    """Structured response produced by the cognitive core."""

    response: str
    model: str
    route: str = "cognitive"
    confidence: Dict = field(default_factory=dict)
    decision: Dict | None = None
    action: Dict | None = None
    cognitive_health: Dict = field(default_factory=dict)
    reflexes: list[Dict] = field(default_factory=list)
    proactive_action: Dict | None = None
    task_plan: Dict | None = None

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
            "model": self.model,
            "route": self.route,
            "confidence": self.confidence,
            "decision": self.decision,
            "action": self.action,
            "cognitive_health": self.cognitive_health,
            "reflexes": self.reflexes,
            "proactive_action": self.proactive_action,
            "task_plan": self.task_plan,
        }


class CognitiveCore:
    """Coordinates the new cognitive modules around the existing MVP."""

    async def processar(
        self,
        mensagem: str,
        *,
        llm,
        memory,
        intent,
        executor: ActionExecutor | None = None,
        dados_sensores: Dict | None = None,
        contexto_extra: Dict | None = None,
        mensagem_llm: str | None = None,
        route: str = "cognitive",
    ) -> ResultadoCognitivo:
        clean_message = (mensagem or "").strip()
        if not clean_message:
            return ResultadoCognitivo(
                response="Envie uma mensagem para eu processar.",
                model=getattr(llm, "model", "desconhecido"),
                route=route,
                cognitive_health=self_monitor.saude_cognitiva(),
            )

        reflexes = []
        if dados_sensores:
            reflexes = fast_thinking.atualizar_sensores(dados_sensores)
            world_model.atualizar_por_sensores(dados_sensores)

        estado_atual = world_model.snapshot()
        world_model.salvar_snapshot()
        contexto = self._build_context(memory, clean_message, contexto_extra, reflexes, estado_atual)
        proactive = goal_system.proxima_acao_proativa(estado_atual)
        if proactive:
            contexto["acao_proativa_sugerida"] = proactive

        task_plan = self._maybe_plan_task(clean_message, contexto)
        if task_plan:
            contexto["plano_tarefa"] = task_plan

        resposta_texto, acao = await intent.processar(
            clean_message,
            contexto,
            llm_message=mensagem_llm,
        )

        decision_payload = None
        action_payload = None
        resultado_acao = None

        if acao:
            decisao = decision_engine.decidir([acao], estado_atual)
            decision_payload = decisao.to_dict()
            if decisao.requer_confirmacao:
                resposta_texto = self._append_confirmation(resposta_texto, decision_payload)
                action_payload = {
                    "type": acao.get("acao"),
                    "status": "requires_confirmation",
                    "decision": decision_payload,
                }
            elif executor:
                resultado_acao = await self._execute(executor, acao)
                resposta_texto = self._append_action_result(resposta_texto, resultado_acao)
                action_payload = {
                    "type": acao.get("acao"),
                    "result": resultado_acao,
                    "decision": decision_payload,
                }
            else:
                action_payload = {
                    "type": acao.get("acao"),
                    "status": "no_executor",
                    "decision": decision_payload,
                }

        confidence_report = self_monitor.avaliar_confianca(resposta_texto, contexto)
        confidence = confidence_report.to_dict()
        monitor_decision = self_monitor.verificar_e_agir(confidence_report, clean_message, contexto)
        if monitor_decision["acao"] == "alertar_usuario" and "Estou um pouco incerto" not in resposta_texto:
            resposta_texto = f"{resposta_texto}\n{monitor_decision['mensagem']}"
        elif monitor_decision["acao"] == "aguardar_instrucao" and "Preciso de ajuda humana" not in resposta_texto:
            resposta_texto = f"{resposta_texto}\n{monitor_decision['mensagem']}"

        episodio = self._build_episode(clean_message, estado_atual, acao, resultado_acao, confidence)
        experience_buffer.registrar(episodio)
        behavior_optimizer.aprender_com_episodio(episodio)

        memory.salvar_conversa(
            clean_message,
            resposta_texto,
            {
                "rota": route,
                "acao": acao,
                "decisao": decision_payload,
                "resultado_acao": resultado_acao,
                "confianca": confidence,
                "reflexos": reflexes,
                "proativa": proactive,
            },
        )

        return ResultadoCognitivo(
            response=resposta_texto,
            model=getattr(llm, "model", "desconhecido"),
            route=route,
            confidence=confidence,
            decision=decision_payload,
            action=action_payload,
            cognitive_health=self_monitor.saude_cognitiva(),
            reflexes=reflexes,
            proactive_action=proactive,
            task_plan=task_plan,
        )

    def health(self) -> Dict:
        return {
            "self_monitor": self_monitor.saude_cognitiva(),
            "fast_thinking": fast_thinking.estado(),
            "goals": goal_system.listar_metas(),
        }

    def start_background_loops(self) -> None:
        """Start cognitive background loops used by the running app."""
        fast_thinking.iniciar_loop(frequencia_hz=100)

    def state(self) -> Dict:
        return {
            "world_model": world_model.resumo(),
            "goals": goal_system.listar_metas(),
            "fast_thinking": fast_thinking.estado(),
            "learning": experience_buffer.metricas(),
        }

    def _build_context(
        self,
        memory,
        message: str,
        extra: Dict | None,
        reflexes: list[Dict],
        estado_atual: Dict,
    ) -> Dict:
        context = memory.gerar_contexto_para_llm(message)
        if extra:
            context.update(extra)
        context["estado_mundo"] = estado_atual
        context["saude_cognitiva"] = self_monitor.saude_cognitiva()
        if reflexes:
            context["reflexos_ativos"] = reflexes
        return context

    def _maybe_plan_task(self, message: str, context: Dict) -> Dict | None:
        lower = message.lower()
        complex_markers = ["pegue", "traga", "entregue", "organize", "inspecione", "navegue"]
        if not any(marker in lower for marker in complex_markers):
            return None
        plan = task_engine.criar_plano(message, context)
        return plan.to_dict()

    async def _execute(self, executor: ActionExecutor, action: Dict) -> Dict:
        result = executor(action)
        if inspect.isawaitable(result):
            result = await result
        return dict(result)

    def _append_confirmation(self, response: str, decision: Dict) -> str:
        reason = decision.get("justificativa", "Confirmacao humana necessaria.")
        return f"{response}\nConfirmacao necessaria: {reason}"

    def _append_action_result(self, response: str, result: Dict) -> str:
        status = result.get("status")
        message = result.get("mensagem", "")
        if status == "success":
            return f"{response}\nOK: {message}"
        if status in {"stub", "needs_input"}:
            return f"{response}\nInfo: {message}"
        return f"{response}\nErro: {message}"

    def _build_episode(
        self,
        message: str,
        estado_atual: Dict,
        action: Dict | None,
        action_result: Dict | None,
        confidence: Dict,
    ) -> Episodio:
        if action_result:
            status = str(action_result.get("status", "unknown"))
            resultado = "sucesso" if status in {"success", "stub", "needs_input"} else "falha"
            reward = 0.8 if resultado == "sucesso" else -0.4
        else:
            resultado = "sucesso"
            reward = 0.2 if not action else 0.0
        reward += (float(confidence.get("score", 0.5)) - 0.5) * 0.2
        return Episodio(
            id=None,
            timestamp=datetime.now().isoformat(),
            contexto={"mensagem": message, "estado": estado_atual},
            acao=str(action.get("acao") if action else "responder"),
            parametros=dict(action.get("parametros", {}) if action else {}),
            resultado=resultado,
            recompensa=max(-1.0, min(1.0, reward)),
        )


cognitive_core = CognitiveCore()
