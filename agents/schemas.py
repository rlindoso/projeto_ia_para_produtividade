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
