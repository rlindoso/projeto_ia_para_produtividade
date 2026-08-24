"""Agente Agile Coach: transforma anotações de reunião em backlog estruturado para GitHub Projects.

Recebe uma transcrição ou anotações em linguagem natural e devolve um
``BacklogEstruturado`` (Pydantic) com épicos, features e stories prontas
para criação no GitHub — títulos, corpos em GFM e configurações do Project.

Como não realiza chamadas externas, o agente usa ``with_structured_output``
diretamente sobre o modelo, sem o grafo LangGraph de tool-calling.
"""

import sys
from functools import lru_cache
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import load_chat_model
from agents.schemas import BacklogEstruturado

_AGENTS_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _AGENTS_DIR.parent


def _carregar_prompt() -> str:
    prompt = (_ROOT_DIR / "agile_coach_prompt.txt").read_text(encoding="utf-8")
    structured_output = (_ROOT_DIR / "agile_coach_structured_output.md").read_text(encoding="utf-8")
    return f"{prompt}\n\n---\n\n### TEMPLATE DO CORPO (FEATURE / STORY)\n\n{structured_output}"


SYSTEM_AGILE_COACH = _carregar_prompt()


class AgileCoachAgent:
    """Agente que transforma reuniões em backlog estruturado via structured output."""

    def __init__(self, model):
        self.model = model.with_structured_output(BacklogEstruturado)

    def invoke(self, transcricao: str) -> BacklogEstruturado:
        messages = [
            SystemMessage(content=SYSTEM_AGILE_COACH),
            HumanMessage(content=transcricao),
        ]
        return self.model.invoke(messages)


@lru_cache(maxsize=1)
def build_agent() -> AgileCoachAgent:
    """Constrói o Agente Agile Coach como singleton."""
    return AgileCoachAgent(load_chat_model())


if __name__ == "__main__":
    transcricao = " ".join(sys.argv[1:]) or (
        "Reunião de planejamento: precisamos corrigir o bug de login que está "
        "causando HTTP 500, atualizar a documentação da API REST e avaliar a "
        "criação de um dashboard de métricas para o time de negócio."
    )

    resultado: BacklogEstruturado = build_agent().invoke(transcricao)

    print(f"\n=== RESUMO DA REUNIÃO ===\n{resultado.resumo_reuniao}\n")
    for issue in resultado.issues:
        print(f"{'=' * 60}")
        print(f"[{issue.tipo.upper()}] {issue.titulo}")
        if issue.epic_pai:
            print(f"Epic pai: {issue.epic_pai}")
        cfg = issue.configuracao_projeto
        print(f"Status: {cfg.status} | Priority: {cfg.priority} | Labels: {', '.join(cfg.labels)}")
        print(f"\n--- Corpo da Issue ---\n{issue.corpo_issue}\n")
