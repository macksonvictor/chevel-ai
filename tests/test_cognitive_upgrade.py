import tempfile
import unittest
from pathlib import Path

from core.cognitive_core import CognitiveCore
from core.decision_engine import DecisionEngine
from core.fast_thinking import FastThinkingSystem
from core.goal_system import GoalSystem
from core.learning_system import BehaviorOptimizer, Episodio, ExperienceBuffer
from core.memory_advanced import MemoriaProcedural, Passo, Procedimento
from core.task_reasoning import TaskReasoningEngine
from core.world_model import ObjetoMundo, WorldModel


class FakeLLM:
    model = "llama3.2:latest"


class FakeMemory:
    def __init__(self):
        self.saved = []

    def gerar_contexto_para_llm(self, message):
        return {"message_seen": message}

    def salvar_conversa(self, user, assistant, context=None):
        self.saved.append((user, assistant, context))


class FakeIntent:
    def __init__(self, response="OK", action=None):
        self.response = response
        self.action = action
        self.last_llm_message = None

    async def processar(self, message, contexto=None, llm_message=None):
        self.last_llm_message = llm_message
        return self.response, self.action


class CognitiveUpgradeTests(unittest.IsolatedAsyncioTestCase):
    async def test_cognitive_core_executes_safe_action_and_saves_episode(self):
        core = CognitiveCore()
        memory = FakeMemory()
        intent = FakeIntent(
            "Executando programa: calc",
            {"tipo": "acao", "acao": "executar_programa", "parametros": {"programa": "calc"}, "confianca": 0.9},
        )

        async def executor(action):
            return {"status": "success", "mensagem": "Programa iniciado"}

        result = await core.processar(
            "abra calculadora",
            llm=FakeLLM(),
            memory=memory,
            intent=intent,
            executor=executor,
        )

        self.assertIn("OK: Programa iniciado", result.response)
        self.assertEqual(result.action["result"]["status"], "success")
        self.assertFalse(result.decision["requer_confirmacao"])
        self.assertEqual(memory.saved[0][0], "abra calculadora")

    async def test_cognitive_core_requires_confirmation_for_robot_action(self):
        core = CognitiveCore()
        intent = FakeIntent(
            "Movendo braco robotico.",
            {"tipo": "acao", "acao": "mover_braco", "parametros": {}, "confianca": 0.9},
        )

        result = await core.processar(
            "mova o braco",
            llm=FakeLLM(),
            memory=FakeMemory(),
            intent=intent,
            executor=lambda action: {"status": "success"},
        )

        self.assertIn("Confirmacao necessaria", result.response)
        self.assertTrue(result.decision["requer_confirmacao"])
        self.assertEqual(result.action["status"], "requires_confirmation")


class CognitiveModuleTests(unittest.TestCase):
    def test_decision_engine_high_risk_requires_confirmation(self):
        decision = DecisionEngine().decidir([
            {"acao": "enviar_email", "parametros": {"destinatario": "a@b.com"}, "confianca": 0.9}
        ])

        self.assertEqual(decision.risco.value, "alto")
        self.assertTrue(decision.requer_confirmacao)

    def test_decision_engine_scores_benefit_urgency_and_critical_confirmation(self):
        engine = DecisionEngine()
        decision = engine.decidir([
            {
                "acao": "executar_programa",
                "parametros": {"programa": "calc & del"},
                "beneficio": 1.0,
                "urgencia": 1.0,
            }
        ])

        self.assertEqual(decision.risco.value, "critico")
        self.assertTrue(decision.requer_confirmacao)
        self.assertIn("Confirmacao humana obrigatoria", decision.justificativa)

    def test_world_model_persists_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = WorldModel(Path(tmp) / "memory.db")
            model.atualizar_sistema("bateria", 75)
            model.atualizar_objeto(ObjetoMundo(id="chave", tipo="ferramenta", estado="disponivel"))
            snapshot_id = model.salvar_snapshot()

            self.assertGreater(snapshot_id, 0)
            self.assertEqual(model.snapshots_recentes(1)[0]["snapshot"]["sistema"]["bateria"], 75)
            model.close()

    def test_procedural_memory_save_recover_and_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = MemoriaProcedural(Path(tmp) / "memory.db")
            procedure = Procedimento(
                nome="pegar_chave",
                descricao="Pegar chave na bancada",
                passos=[Passo(1, "Localizar chave", "visao_detectar")],
            )
            memory.salvar(procedure)

            recovered = memory.recuperar("pegar_chave")
            self.assertIsNotNone(recovered)
            self.assertEqual(recovered.passos[0].acao, "visao_detectar")
            memory.close()

    def test_learning_records_and_recommends(self):
        with tempfile.TemporaryDirectory() as tmp:
            buffer = ExperienceBuffer(Path(tmp) / "memory.db")
            optimizer = BehaviorOptimizer(buffer)
            episode = Episodio(
                id=None,
                timestamp="2026-01-01T00:00:00",
                contexto={"estado": "teste"},
                acao="pegar_direto",
                parametros={},
                resultado="sucesso",
                recompensa=0.9,
            )
            buffer.registrar(episode)
            optimizer.aprender_com_episodio(episode)

            self.assertEqual(
                optimizer.recomendar_acao(["pegar_direto", "pegar_com_inspecao"], {"estado": "teste"}),
                "pegar_direto",
            )
            buffer.close()

    def test_task_reasoning_creates_pick_plan(self):
        plan = TaskReasoningEngine().criar_plano("Pegue a chave inglesa", {"objeto": "chave_inglesa"})

        self.assertEqual(plan.subtarefas[0].acao, "visao_detectar")
        self.assertFalse(TaskReasoningEngine().verificar_conclusao(plan))

    def test_fast_thinking_reflex(self):
        fast = FastThinkingSystem()
        reflexes = fast.atualizar_sensores({"bateria": 8})

        self.assertTrue(any(item["acao"]["tipo"] == "parada_emergencia" for item in reflexes))

    def test_goal_system_proactive_battery_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            goals = GoalSystem(Path(tmp) / "memory.db")
            action = goals.proxima_acao_proativa({"sistema": {"bateria": 12}, "pessoas_presentes": []})

            self.assertEqual(action["acao_sugerida"]["acao"], "pausar_operacoes")
            goals.close()


if __name__ == "__main__":
    unittest.main()
