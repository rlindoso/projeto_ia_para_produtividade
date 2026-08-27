"""Agente Orquestrador: consome agentes especialistas como ferramentas.

Cada agente especializado é exposto como uma tool para o grafo LangGraph.
A resposta final de cada subagente é devolvida ao orquestrador, que decide
se precisa delegar mais alguma tarefa ou responder ao usuário.

Fluxo padrão: o Agente de Transcrição limpa a conversa, o Agente Agile Coach
estrutura o backlog, o Agente GitHub cria e organiza as issues e, ao final,
o orquestrador chama o Agente Slack para comunicar à equipe um resumo.

Para adicionar um novo especialista, crie o agente em ``agents/``, envolva-o
em uma ``@tool`` (como ``agente_github``) e registre-a em ``AGENTES_ORQUESTRADOS``.
"""

import sys
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from agents.agent_agile_coach import (
    build_agent as build_agile_coach_agent,
    formatar_backlog,
)
from agents.agent_github import build_agent as build_github_agent
from agents.agent_slack import build_agent as build_slack_agent
from agents.agent_transcricao import (
    build_agent as build_transcricao_agent,
    extrair_briefing,
)
from agents.base import Agent, load_chat_model


@lru_cache(maxsize=1)
def _agente_transcricao():
    return build_transcricao_agent()


@lru_cache(maxsize=1)
def _agente_agile_coach():
    return build_agile_coach_agent()


@lru_cache(maxsize=1)
def _agente_github():
    return build_github_agent()


@lru_cache(maxsize=1)
def _agente_slack():
    return build_slack_agent()


@tool
def agente_transcricao(solicitacao: str) -> str:
    """Delega a solicitação ao Agente de Transcrição, especialista em limpar conversas.

    Use quando a entrada for áudio, arquivo de transcrição, ata de reunião ou conversa bruta.
    O agente divide em tópicos, exclui o que não é o contexto principal e devolve um
    briefing com o prompt para o próximo agente criar tasks. Passe o pedido completo,
    incluindo o caminho do arquivo ou o texto da conversa.
    """
    resultado = _agente_transcricao().invoke(solicitacao)
    briefing = extrair_briefing(resultado)
    if briefing is None:
        return resultado["messages"][-1].content
    return (
        "Briefing da transcrição (insumo para o agente_agile_coach):\n"
        f"{briefing.model_dump_json(ensure_ascii=False, indent=2)}"
    )


@tool
def agente_agile_coach(solicitacao: str) -> str:
    """Delega ao Agente Agile Coach, especialista em transformar reuniões em backlog estruturado para GitHub Projects.

    Use o briefing do agente_transcricao (tópicos e prompt_for_task_agent) ou, se a
    transcrição já estiver limpa, o texto da reunião. A resposta retorna um backlog
    com épicos, features e stories prontos para criar no GitHub.
    """
    resultado = _agente_agile_coach().invoke(solicitacao)
    return formatar_backlog(resultado)


@tool
def agente_github(solicitacao: str) -> str:
    """Delega a solicitação ao Agente GitHub, especialista em Issues e Projects (Kanban) do repositório.

    Use quando o usuário pedir para criar, consultar, atualizar ou fechar issues,
    comentar em issues, adicionar cards ao Project ou mover tarefas entre colunas.
    Passe a instrução completa em linguagem natural; a resposta já vem pronta em português.
    """
    resultado = _agente_github().invoke(solicitacao)
    return resultado["messages"][-1].content


@tool
def agente_slack(solicitacao: str) -> str:
    """Delega a solicitação ao Agente Slack, especialista em comunicação com a equipe.

    Use para enviar mensagens, notificações e resumos das ações executadas ao canal do Slack.
    Passe o conteúdo completo da mensagem/resumo que deve ser enviado; a resposta confirma o envio.
    """
    resultado = _agente_slack().invoke(solicitacao)
    return resultado["messages"][-1].content


AGENTES_ORQUESTRADOS = [
    agente_transcricao,
    agente_agile_coach,
    agente_github,
    agente_slack,
]

SYSTEM_PROMPT = Path("prompts/orchestrator_prompt.txt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def build_orchestrator() -> Agent:
    """Constrói o Agente Orquestrador (grafo compilado) como singleton."""
    return Agent(
        load_chat_model(),
        AGENTES_ORQUESTRADOS,
        system=SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or (
        "Precisamos documentar a API do projeto. "
        "Crie essa tarefa no GitHub e coloque no Kanban."
    )
    resultado = build_orchestrator().invoke(pergunta)
    print(resultado["messages"][-1].content)