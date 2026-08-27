"""Agente Slack: comunica resultados e notificações à equipe.

Seguindo o padrão da aula 05, cada ferramenta recebe a solicitação em
linguagem natural, extrai os parâmetros com classes Pydantic
(``agents/schemas.py`` + ``with_structured_output``) e então executa a
operação correspondente na classe ``SlackTools`` (tools/slack_tools.py).
"""

import sys
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool
from pydantic import BaseModel

from agents.base import Agent, anunciar_ferramenta, extrair_parametros, load_chat_model
from agents.schemas import EnviarMensagemSlackRequest
from tools.slack_tools import SlackTools

slack = SlackTools()


@tool
def enviar_mensagem(mensagem_usuario: str) -> dict:
    """Envia uma mensagem de texto para um canal do Slack; sem canal informado, usa o canal padrão."""
    params: EnviarMensagemSlackRequest = extrair_parametros(
        EnviarMensagemSlackRequest,
        "Extraia a mensagem que deve ser enviada ao Slack. Se a solicitação "
        "contiver um resumo ou resultado, use-o como conteúdo da mensagem; "
        "se um canal específico for citado, extraia seu ID.",
        mensagem_usuario,
    )
    if not params.message.strip():
        raise ValueError("Não foi possível identificar a mensagem a ser enviada.")
    anunciar_ferramenta("enviar_mensagem", params)
    return slack.send_message(params.channel, params.message)


TOOLS_SLACK = [
    enviar_mensagem,
]

SYSTEM_PROMPT = Path("prompts/slack_prompt.txt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def build_agent() -> Agent:
    """Constrói o Agente Slack (grafo compilado) como singleton."""
    return Agent(load_chat_model(), TOOLS_SLACK, system=SYSTEM_PROMPT)


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or (
        "Avise a equipe que o pipeline de tarefas foi concluído com sucesso."
    )
    resultado = build_agent().invoke(pergunta)
    print(resultado["messages"][-1].content)