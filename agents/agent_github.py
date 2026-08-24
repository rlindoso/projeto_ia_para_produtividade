"""Agente GitHub: gerencia Issues e Projects (Kanban) do GitHub.

Seguindo o padrão da aula 05, cada ferramenta recebe a solicitação do
usuário em linguagem natural, extrai os parâmetros com classes Pydantic
(``agents/schemas.py`` + ``with_structured_output``) e então executa a
operação correspondente na classe ``GithubTools`` (tools/github_tools.py).
"""

import sys
from functools import lru_cache

from langchain_core.tools import tool
from pydantic import BaseModel

from agents.base import Agent, anunciar_ferramenta, extrair_parametros, load_chat_model
from agents.schemas import (
    AtualizarIssueRequest,
    ComentarIssueRequest,
    CriarIssueNoProjectRequest,
    CriarIssueRequest,
    FecharIssueRequest,
    MoverNoKanbanRequest,
    NumeroIssueRequest,
)
from tools.github_tools import GithubTools

github = GithubTools()


def _exigir_numero_issue(params: BaseModel) -> int:
    issue_number = getattr(params, "issue_number", None)
    if issue_number is None:
        raise ValueError(
            "Não foi possível identificar o número da issue na mensagem. "
            "Informe a solicitação citando a issue pelo número, por exemplo '#12'."
        )
    return issue_number


@tool
def obter_info_repositorio(mensagem_usuario: str) -> dict:
    """Consulta as informações gerais do repositório configurado."""
    anunciar_ferramenta("obter_info_repositorio")
    return github.get_repo_info()


@tool
def consultar_issue(mensagem_usuario: str) -> dict:
    """Consulta uma issue pelo número e retorna título, descrição, estado, labels, responsáveis e URL."""
    params: NumeroIssueRequest = extrair_parametros(
        NumeroIssueRequest,
        "Extraia o número da issue citado na mensagem. Considere formatos como "
        "'#123', 'issue 123' ou 'issue número 123'. Se não houver número, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("consultar_issue", params)
    return github.get_issue(_exigir_numero_issue(params))


@tool
def criar_issue(mensagem_usuario: str) -> dict:
    """Cria uma issue a partir do título, descrição, labels e responsáveis informados pelo usuário."""
    params: CriarIssueRequest = extrair_parametros(
        CriarIssueRequest,
        "Extraia os dados para criar uma issue. O título é obrigatório; se algum "
        "campo opcional não for mencionado, retorne None.",
        mensagem_usuario,
    )
    if not params.title.strip():
        raise ValueError("Não foi possível identificar o título da issue.")
    anunciar_ferramenta("criar_issue", params)
    return github.create_issue(
        params.title,
        params.body,
        params.labels,
        params.assignees,
        skip_existing=True,
    )


@tool
def atualizar_issue(mensagem_usuario: str) -> dict:
    """Atualiza campos de uma issue existente; apenas os campos que o usuário pediu para alterar são modificados."""
    params: AtualizarIssueRequest = extrair_parametros(
        AtualizarIssueRequest,
        "Extraia a atualização solicitada para a issue. Preencha somente os campos "
        "que o usuário quer alterar; mantenha None nos demais. Se não houver número "
        "de issue na mensagem, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("atualizar_issue", params)
    return github.update_issue(
        _exigir_numero_issue(params),
        params.title,
        params.body,
        params.labels,
        params.assignees,
    )


@tool
def fechar_issue(mensagem_usuario: str) -> dict:
    """Fecha uma issue com motivo 'completed' quando concluída ou 'not_planned' quando não será feita."""
    params: FecharIssueRequest = extrair_parametros(
        FecharIssueRequest,
        "Extraia o número da issue a ser fechada e o motivo. Use 'completed' se foi "
        "concluída ou 'not_planned' se não será feita; sem indicação, use 'completed'. "
        "Se não houver número de issue na mensagem, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("fechar_issue", params)
    return github.close_issue(_exigir_numero_issue(params), params.reason)


@tool
def comentar_issue(mensagem_usuario: str) -> dict:
    """Adiciona um comentário em texto livre em uma issue."""
    params: ComentarIssueRequest = extrair_parametros(
        ComentarIssueRequest,
        "Extraia o número da issue e o texto do comentário que o usuário deseja "
        "publicar. Se não houver número de issue na mensagem, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("comentar_issue", params)
    return github.add_comment(_exigir_numero_issue(params), params.body)


@tool
def adicionar_ao_project(mensagem_usuario: str) -> dict:
    """Adiciona uma issue existente ao Project (Kanban) configurado."""
    params: NumeroIssueRequest = extrair_parametros(
        NumeroIssueRequest,
        "Extraia o número da issue que deve ser adicionada ao Project. "
        "Se não houver número na mensagem, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("adicionar_ao_project", params)
    return github.add_issue_to_project(_exigir_numero_issue(params))


@tool
def listar_campos_project(mensagem_usuario: str) -> list[dict]:
    """Lista os campos do Project, incluindo as opções válidas do campo Status do Kanban."""
    anunciar_ferramenta("listar_campos_project")
    return github.get_project_fields()


@tool
def mover_no_kanban(mensagem_usuario: str) -> dict:
    """Move uma issue que já está no Project para a coluna/status informado, por exemplo Todo, In Progress ou Done."""
    params: MoverNoKanbanRequest = extrair_parametros(
        MoverNoKanbanRequest,
        "Extraia o número da issue e o nome da coluna de destino no Kanban "
        "(por exemplo Todo, In Progress ou Done). Se não houver número de issue "
        "na mensagem, retorne null.",
        mensagem_usuario,
    )
    anunciar_ferramenta("mover_no_kanban", params)
    return github.move_issue(_exigir_numero_issue(params), params.status)


@tool
def criar_issue_no_project(mensagem_usuario: str) -> dict:
    """Fluxo completo de criação: cria a issue, adiciona ao Project e define o status inicial no Kanban."""
    params: CriarIssueNoProjectRequest = extrair_parametros(
        CriarIssueNoProjectRequest,
        "Extraia os dados para criar uma issue e adicioná-la ao Project. O título é "
        "obrigatório; status inicial e labels são opcionais e devem ser None se não forem informados.",
        mensagem_usuario,
    )
    if not params.title.strip():
        raise ValueError("Não foi possível identificar o título da issue.")
    anunciar_ferramenta("criar_issue_no_project", params)
    return github.create_issue_and_add_to_project(
        title=params.title,
        body=params.body,
        status=params.status,
        labels=params.labels,
    )


TOOLS_GITHUB = [
    obter_info_repositorio,
    consultar_issue,
    criar_issue,
    atualizar_issue,
    fechar_issue,
    comentar_issue,
    adicionar_ao_project,
    listar_campos_project,
    mover_no_kanban,
    criar_issue_no_project,
]

SYSTEM_AGENT_GITHUB = """Você é um Agente GitHub especializado em gerenciar Issues e o Project (Kanban) do repositório configurado.

Diretrizes:
- Para solicitações do tipo "crie uma tarefa/issue e coloque no quadro", SEMPRE use criar_issue_no_project, que cria a issue e posiciona o card em uma única chamada. Não combine criar_issue com adicionar_ao_project nesse caso.
- Use criar_issue quando for pedido apenas para abrir a issue, sem Kanban.
- Use adicionar_ao_project e mover_no_kanban para organizar issues já existentes.
- Antes de mover no Kanban, se tiver dúvida sobre os nomes válidos das colunas, use listar_campos_project.
- Use consultar_issue antes de atualizar ou fechar quando não souber o estado atual da issue.
- Ao chamar uma ferramenta, repasse a solicitação completa e fiel ao usuário: as ferramentas extraem automaticamente os parâmetros necessários.
- IMPORTANTE: quando uma ferramenta retornar o número de uma issue (por exemplo 12), cite-o explicitamente nas mensagens seguintes usando o formato '#12' (ex.: "Mova a issue #12 para Todo"). Nunca deixe de informar o número quando ele for conhecido; nunca invente um número.
- CADA tarefa solicitada deve gerar exatamente UMA issue. Depois que criar_issue ou criar_issue_no_project retornar sucesso, não chame criação novamente para a mesma tarefa; se precisar ajustar algo, use atualizar_issue.
- Se o resultado indicar "ja_existia": true, a issue já existia e foi reaproveitada: informe isso ao usuário e siga adiante, sem criar outra.
- Nunca invente números de issue, URLs, IDs, cotações ou resultados: use somente os dados devolvidos pelas ferramentas.
- Se uma ferramenta retornar erro, leia a mensagem de erro e corrija a chamada antes de tentar novamente.
- Responda em português."""


@lru_cache(maxsize=1)
def build_agent() -> Agent:
    """Constrói o Agente GitHub (grafo compilado) como singleton."""
    return Agent(load_chat_model(), TOOLS_GITHUB, system=SYSTEM_AGENT_GITHUB)


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or (
        "Crie uma issue com o título 'Testar o Agente GitHub', "
        "adicione-a ao Project e deixe-a na coluna Todo."
    )
    resultado = build_agent().invoke(pergunta)
    print(resultado["messages"][-1].content)
