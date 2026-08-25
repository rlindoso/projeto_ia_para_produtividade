"""Classes base para extração estruturada dos parâmetros das ferramentas.

Seguindo o padrão da aula 05, cada ferramenta recebe a mensagem do usuário
em linguagem natural e utiliza um modelo Pydantic com
``chat.with_structured_output`` para extrair os parâmetros necessários
antes de chamar a API.
"""

from pydantic import BaseModel, Field


class NumeroIssueRequest(BaseModel):
    issue_number: int | None = Field(
        None,
        description="Número da issue, por exemplo 123 para '#123'; None se não houver número na mensagem.",
    )


class CriarIssueRequest(BaseModel):
    title: str = Field(..., description="Título curto e objetivo da issue.")
    body: str | None = Field(None, description="Descrição detalhada da issue.")
    labels: list[str] | None = Field(None, description="Rótulos da issue, por exemplo bug ou documentation.")
    assignees: list[str] | None = Field(None, description="Logins do GitHub dos responsáveis pela issue.")


class AtualizarIssueRequest(BaseModel):
    issue_number: int | None = Field(
        None,
        description="Número da issue a ser atualizada; None se não houver número na mensagem.",
    )
    title: str | None = Field(None, description="Novo título; None se não for alterado.")
    body: str | None = Field(None, description="Nova descrição; None se não for alterada.")
    labels: list[str] | None = Field(None, description="Novos rótulos; None se não forem alterados.")
    assignees: list[str] | None = Field(None, description="Novos responsáveis; None se não forem alterados.")


class FecharIssueRequest(BaseModel):
    issue_number: int | None = Field(
        None,
        description="Número da issue a ser fechada; None se não houver número na mensagem.",
    )
    reason: str = Field(
        "completed",
        description="'completed' quando a issue foi concluída ou 'not_planned' quando não será feita.",
    )


class ComentarIssueRequest(BaseModel):
    issue_number: int | None = Field(
        None,
        description="Número da issue que receberá o comentário; None se não houver número na mensagem.",
    )
    body: str = Field(..., description="Texto do comentário a ser adicionado.")


class MoverNoKanbanRequest(BaseModel):
    issue_number: int | None = Field(
        None,
        description="Número da issue que será movida no Kanban; None se não houver número na mensagem.",
    )
    status: str = Field(
        ...,
        description="Nome da coluna de destino no Project, por exemplo Todo, In Progress ou Done.",
    )


class CriarIssueNoProjectRequest(BaseModel):
    title: str = Field(..., description="Título curto e objetivo da issue.")
    body: str | None = Field(None, description="Descrição detalhada da issue.")
    status: str | None = Field(
        None,
        description="Coluna inicial no Kanban, por exemplo Todo; None se o usuário não informar.",
    )
    labels: list[str] | None = Field(None, description="Rótulos da issue, por exemplo bug ou documentation.")


class EnviarMensagemSlackRequest(BaseModel):
    message: str = Field(..., description="Texto da mensagem que será enviada ao canal do Slack.")
    channel: str | None = Field(
        None,
        description="ID do canal de destino, por exemplo C0123456789; None para usar o canal padrão.",
    )


class TranscreverAudioRequest(BaseModel):
    path: str = Field(..., description="Caminho do arquivo de áudio a ser transcrito.")
    language: str = Field(
        "pt",
        description="Código de idioma da transcrição, por exemplo pt.",
    )


class CarregarTextoRequest(BaseModel):
    path: str = Field(
        ...,
        description="Caminho do arquivo de texto ou transcrição, relativo à raiz do projeto ou absoluto.",
    )


class TopicoTranscricao(BaseModel):
    title: str = Field(..., description="Nome curto do tópico.")
    summary: str = Field(..., description="O que foi decidido ou pedido neste tópico.")
    excerpts: list[str] = Field(
        ...,
        description="Trechos da conversa que sustentam o tópico.",
    )


class BriefingTranscricao(BaseModel):
    main_context: str = Field(..., description="Tema central da conversa em uma frase.")
    discarded: list[str] = Field(..., description="O que foi excluído e por quê.")
    topics: list[TopicoTranscricao] = Field(
        ...,
        description="Tópicos do contexto principal, sem ruído nem assuntos paralelos.",
    )
    prompt_for_task_agent: str = Field(
        ...,
        description="Prompt autocontido em português (Task, Context, Instructions) para o agente que cria tasks.",
    )


class ConfiguracaoProjeto(BaseModel):
    status: str = Field(..., description="Status no Kanban, ex: Todo, In Progress, Done, Backlog.")
    priority: str = Field(..., description="Prioridade: High, Medium ou Low.")
    type: str = Field(..., description="Tipo do item: Epic, Feature, Story, Bug ou Task.")
    labels: list[str] = Field(default_factory=list, description="Labels do GitHub, ex: ['epic', 'backend'].")


class IssueBacklog(BaseModel):
    tipo: str = Field(..., description="Tipo do item: epic, feature, story, bug ou task.")
    titulo: str = Field(..., description="Título da issue no GitHub, curto e direto.")
    epic_pai: str | None = Field(
        None,
        description="Título do épico pai ao qual esta issue pertence; None se for o próprio épico.",
    )
    configuracao_projeto: ConfiguracaoProjeto
    corpo_issue: str = Field(
        ...,
        description="Corpo completo da issue em GitHub Flavored Markdown, pronto para colar no GitHub.",
    )


class BacklogEstruturado(BaseModel):
    resumo_reuniao: str = Field(..., description="Resumo executivo dos pontos discutidos na reunião.")
    issues: list[IssueBacklog] = Field(
        ...,
        description="Lista de issues geradas, ordenadas: épicos primeiro, depois features e stories filhas.",
    )
