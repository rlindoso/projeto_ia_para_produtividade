"""Agente Orquestrador: consome agentes especialistas como ferramentas.

Cada agente especializado é exposto como uma tool para o grafo LangGraph.
A resposta final de cada subagente é devolvida ao orquestrador, que decide
se precisa delegar mais alguma tarefa ou responder ao usuário.

Fluxo padrão: os especialistas executam as ações (por exemplo, o Agente
GitHub cria e organiza as issues) e, ao final, o orquestrador chama o
Agente Slack para comunicar à equipe um resumo do que foi feito.

Para adicionar um novo especialista, crie o agente em ``agents/``, envolva-o
em uma ``@tool`` (como ``agente_github``) e registre-a em ``AGENTES_ORQUESTRADOS``.
"""

import sys
from functools import lru_cache

from langchain_core.tools import tool

from agents.agent_agile_coach import build_agent as build_agile_coach_agent
from agents.agent_github import build_agent as build_github_agent
from agents.agent_slack import build_agent as build_slack_agent
from agents.base import Agent, load_chat_model


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
def agente_agile_coach(solicitacao: str) -> str:
    """Delega ao Agente Agile Coach, especialista em transformar reuniões em backlog estruturado para GitHub Projects.

    Use quando o usuário fornecer anotações, transcrições ou resumos de reunião e pedir para gerar
    épicos, features ou stories prontos para criar no GitHub. Passe o texto completo da reunião;
    a resposta retorna um backlog estruturado com títulos, corpos GFM e configurações do Project.
    """
    resultado = _agente_agile_coach().invoke(solicitacao)
    issues_resumo = "\n".join(
        f"- [{i.tipo.upper()}] {i.titulo}" for i in resultado.issues
    )
    return (
        f"Resumo da reunião: {resultado.resumo_reuniao}\n\n"
        f"Issues geradas ({len(resultado.issues)}):\n{issues_resumo}\n\n"
        f"Backlog completo disponível para criação no GitHub."
    )


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
    agente_agile_coach,
    agente_github,
    agente_slack,
]

SYSTEM_AGENT_ORQUESTRADOR = """Você é um Agente Orquestrador de um pipeline de produtividade.

Você não executa operações diretamente: seu papel é analisar a mensagem do usuário e delegar o trabalho aos agentes especialistas disponíveis como ferramentas.

Agentes disponíveis:
- agente_agile_coach: transforma anotações ou transcrições de reunião em backlog estruturado (épicos, features, stories) com corpo GFM e configurações para GitHub Projects. Use quando o usuário fornecer texto de reunião e pedir geração de tarefas/backlog.
- agente_github: gerencia Issues e Projects (Kanban) no GitHub. Use para criar, consultar, atualizar, fechar ou comentar em issues e para organizar cards no quadro.
- agente_slack: comunica a equipe via Slack. Use para enviar mensagens, notificações e resumos.

Regras:
- Escolha sempre o agente especialista adequado à intenção do usuário.
- Se mais de um agente for necessário, chame-os na ordem que fizer sentido, passando para cada um todas as informações de que precisar.
- Ao passar uma solicitação a um agente, seja completo e explícito: inclua títulos, descrições, status e qualquer contexto relevante da mensagem original.
- Se o usuário pedir VÁRIAS tarefas para o mesmo especialista, delegue todas em UMA ÚNICA chamada (liste as tarefas na solicitação), em vez de chamar o agente uma vez por tarefa. Cada tarefa deve virar uma única issue, sem duplicatas.
- FECHAMENTO OBRIGATÓRIO: sempre que a orquestração executar ações por meio dos especialistas (por exemplo, issues criadas, atualizadas ou movidas), finalize chamando o agente_slack com um resumo objetivo do que foi feito — incluindo números das issues, URLs e status no Kanban — antes de responder ao usuário. Não envie resumo se nenhuma ação foi executada.
- Não invente resultados: baseie a resposta final apenas no que os agentes retornarem.
- Se nenhum agente cobrir a solicitação, informe isso claramente ao usuário, sem tentar executar a tarefa.
- Responda em português."""


@lru_cache(maxsize=1)
def build_orchestrator() -> Agent:
    """Constrói o Agente Orquestrador (grafo compilado) como singleton."""
    return Agent(
        load_chat_model(),
        AGENTES_ORQUESTRADOS,
        system=SYSTEM_AGENT_ORQUESTRADOR,
    )


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or (
        "Precisamos documentar a API do projeto. "
        "Crie essa tarefa no GitHub e coloque no Kanban."
    )
    resultado = build_orchestrator().invoke(pergunta)
    print(resultado["messages"][-1].content)
