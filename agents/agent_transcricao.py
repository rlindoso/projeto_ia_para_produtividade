"""Agente de transcrição: limpa o contexto e prepara o prompt do próximo agente.

Recebe áudio ou texto, divide a conversa em tópicos, exclui o que não é o
contexto principal e estrutura um prompt para o agente que cria tasks.

Ele **não cria tasks**.
"""

import json
import sys
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from agents.base import Agent, anunciar_ferramenta, extrair_parametros, load_chat_model
from agents.schemas import (
    BriefingTranscricao,
    CarregarTextoRequest,
    TranscreverAudioRequest,
)
from tools.transcription_tools import TranscriptionTools

transcription = TranscriptionTools()

INSTRUCAO_BRIEFING = (
    "Analise a conversa ou transcrição. Extraia o contexto principal, liste o "
    "que deve ser descartado e por quê, e divida o restante em tópicos (título, "
    "resumo do que foi decidido ou pedido, trechos que sustentam). "
    "O campo prompt_for_task_agent pode ficar vazio: ele será montado em código. "
    "Não invente conteúdo. Não escreva tasks, tickets nem checklists. "
    "Exclua small talk, retratações, tentativas abortadas e assuntos paralelos."
)


def formatar_prompt_para_agile(briefing: BriefingTranscricao) -> str:
    """Monta o XML autocontido que o Agente Agile Coach deve receber."""
    topicos = "\n".join(
        f"- {topic.title}: {topic.summary}\n"
        f"  Trechos: {' | '.join(topic.excerpts)}"
        for topic in briefing.topics
    )
    descartados = "\n".join(f"- {item}" for item in briefing.discarded) or "- (nada)"
    return f"""<Task>
Transformar este briefing em backlog ágil para GitHub Projects: épicos, features e stories.
Não crie issues no GitHub. Só estruture o backlog.
</Task>

<Context>
Contexto principal: {briefing.main_context}

Tópicos do contexto principal:
{topicos}

Fora de escopo (não virar issue):
{descartados}
</Context>

<Instructions>
- Use somente o que está em Context. O próximo agente não verá a conversa original.
- Não invente requisitos, prazos nem responsáveis que não estejam nos tópicos.
- Não gere issues para o que está fora de escopo.
- Produza épicos, features e stories com corpo em GitHub Flavored Markdown e metadados do Project.
</Instructions>
"""


def extrair_briefing(resultado: dict) -> BriefingTranscricao | None:
    """Recupera o BriefingTranscricao devolvido pela tool estruturar_conversa."""
    for msg in resultado.get("messages", []):
        if getattr(msg, "name", None) != "estruturar_conversa":
            continue
        try:
            data = json.loads(msg.content)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("topics"):
            return BriefingTranscricao.model_validate(data)
    return None


@tool
def transcrever_audio(mensagem_usuario: str) -> dict:
    """Transcreve um arquivo de áudio para texto; use quando a entrada for áudio."""
    params: TranscreverAudioRequest = extrair_parametros(
        TranscreverAudioRequest,
        "Extraia o caminho do arquivo de áudio (por exemplo .mp3, .wav, .m4a, .webm) "
        "e o idioma se for citado. Sem idioma, use pt.",
        mensagem_usuario,
    )
    if not params.path.strip():
        raise ValueError("Não foi possível identificar o caminho do arquivo de áudio.")
    anunciar_ferramenta("transcrever_audio", params)
    texto = transcription.transcribe_audio(params.path, params.language)
    return {"texto": texto}


@tool
def carregar_transcricao(mensagem_usuario: str) -> dict:
    """Lê um arquivo de texto ou transcrição do disco; use quando o usuário informar um caminho .txt."""
    params: CarregarTextoRequest = extrair_parametros(
        CarregarTextoRequest,
        "Extraia o caminho do arquivo de texto ou transcrição citado na mensagem. "
        "Pode ser relativo à raiz do projeto, por exemplo docs/transcricao_feature_teleconsulta.txt.",
        mensagem_usuario,
    )
    if not params.path.strip():
        raise ValueError("Não foi possível identificar o caminho do arquivo de texto.")
    anunciar_ferramenta("carregar_transcricao", params)
    return {"texto": transcription.load_text(params.path)}


@tool
def estruturar_conversa(mensagem_usuario: str) -> dict:
    """Divide a conversa em tópicos do contexto principal, descarta ruído e monta o prompt para o agente de tasks."""
    briefing: BriefingTranscricao = extrair_parametros(
        BriefingTranscricao,
        INSTRUCAO_BRIEFING,
        mensagem_usuario,
    )
    if not briefing.topics:
        raise ValueError("Não foi possível identificar tópicos no contexto principal da conversa.")
    briefing.prompt_for_task_agent = formatar_prompt_para_agile(briefing)
    anunciar_ferramenta("estruturar_conversa", briefing)
    return briefing.model_dump()


TOOLS_TRANSCRICAO = [
    transcrever_audio,
    carregar_transcricao,
    estruturar_conversa,
]

SYSTEM_PROMPT = Path("prompts/transcricao_prompt.txt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def build_agent() -> Agent:
    """Constrói o Agente de Transcrição (grafo compilado) como singleton."""
    return Agent(load_chat_model(), TOOLS_TRANSCRICAO, system=SYSTEM_PROMPT)


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or (
        "Estruture a transcrição em docs/transcricao_feature_teleconsulta.txt "
        "para o próximo agente criar tasks."
    )
    resultado = build_agent().invoke(pergunta)
    print(resultado["messages"][-1].content)