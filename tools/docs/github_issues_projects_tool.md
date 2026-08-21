# GitHub Issues & Projects Tool — Guia de Implementação

## Objetivo

Criar uma **Tool em Python** responsável por automatizar o gerenciamento de Issues e Projects do GitHub.

A Tool deverá permitir:

- Criar Issues
- Editar Issues
- Fechar Issues
- Adicionar Issues a um Project
- Mover Issues entre as colunas/status do Kanban
- Adicionar comentários nas Issues
- Consultar informações necessárias para executar essas operações

---

## 1. Arquitetura

```text
Agente / LLM
     │
     ▼
GitHubIssuesTool
     │
     ├── create_issue()
     ├── update_issue()
     ├── close_issue()
     ├── add_issue_to_project()
     ├── move_issue()
     └── add_comment()
            │
            ▼
       GitHub API
       ├── REST API
       └── GraphQL API
```

### REST x GraphQL

| Operação | API |
|---|---|
| Criar Issue | REST |
| Editar Issue | REST |
| Fechar Issue | REST |
| Adicionar comentário | REST |
| Adicionar ao Project | GraphQL |
| Consultar campos do Project | GraphQL |
| Mover entre colunas | GraphQL |

---

# 2. Configuração

A Tool deve receber as configurações através de variáveis de ambiente.

```env
GITHUB_TOKEN=ghp_xxxxxxxxx
GITHUB_OWNER=minha-organizacao
GITHUB_REPOSITORY=meu-repositorio
GITHUB_PROJECT_ID=PVT_xxxxxxxxx
```

Recomenda-se **não colocar o token diretamente no código**.

---

# 3. Dependências

Uma implementação simples pode utilizar:

```bash
pip install requests
```

Estrutura sugerida:

```text
github_tool/
├── __init__.py
├── github_client.py
├── github_tool.py
├── models.py
└── config.py
```

---

# 4. Cliente GitHub

Criar uma classe responsável pela comunicação com a API.

```python
import os
import requests


class GitHubClient:

    def __init__(self):
        self.token = os.environ["GITHUB_TOKEN"]

        self.rest_url = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    def rest_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ):
        response = requests.request(
            method,
            f"{self.rest_url}{endpoint}",
            headers=self.headers,
            **kwargs
        )

        response.raise_for_status()

        if response.status_code == 204:
            return None

        return response.json()

    def graphql_request(
        self,
        query: str,
        variables: dict | None = None
    ):
        response = requests.post(
            self.graphql_url,
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "variables": variables or {},
            }
        )

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            raise RuntimeError(data["errors"])

        return data["data"]
```

---

# 5. Criar Issue

## Endpoint

```http
POST /repos/{owner}/{repo}/issues
```

Payload:

```json
{
  "title": "Corrigir erro no login",
  "body": "O endpoint de login está retornando erro 500.",
  "labels": [
    "bug"
  ],
  "assignees": [
    "usuario"
  ]
}
```

Implementação:

```python
def create_issue(
    self,
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
):
    payload = {
        "title": title,
    }

    if body:
        payload["body"] = body

    if labels:
        payload["labels"] = labels

    if assignees:
        payload["assignees"] = assignees

    return self.client.rest_request(
        "POST",
        f"/repos/{self.owner}/{self.repository}/issues",
        json=payload,
    )
```

### Informações importantes do retorno

Guardar principalmente:

```text
id
node_id
number
html_url
```

O `node_id` será necessário para trabalhar com o Project via GraphQL.

---

# 6. Editar Issue

## Endpoint

```http
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

Campos que podem ser alterados:

```text
title
body
state
state_reason
assignees
labels
milestone
```

Implementação:

```python
def update_issue(
    self,
    issue_number: int,
    title: str | None = None,
    body: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
):
    payload = {}

    if title is not None:
        payload["title"] = title

    if body is not None:
        payload["body"] = body

    if labels is not None:
        payload["labels"] = labels

    if assignees is not None:
        payload["assignees"] = assignees

    return self.client.rest_request(
        "PATCH",
        f"/repos/{self.owner}/{self.repository}/issues/{issue_number}",
        json=payload,
    )
```

---

# 7. Fechar Issue

Fechar uma Issue é alterar seu estado:

```json
{
  "state": "closed"
}
```

Implementação:

```python
def close_issue(
    self,
    issue_number: int,
    reason: str = "completed",
):
    return self.client.rest_request(
        "PATCH",
        f"/repos/{self.owner}/{self.repository}/issues/{issue_number}",
        json={
            "state": "closed",
            "state_reason": reason,
        },
    )
```

Os valores recomendados para `state_reason` incluem:

```text
completed
not_planned
```

---

# 8. Adicionar comentário

## Endpoint

```http
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
```

Payload:

```json
{
  "body": "Implementação concluída."
}
```

Implementação:

```python
def add_comment(
    self,
    issue_number: int,
    body: str,
):
    return self.client.rest_request(
        "POST",
        f"/repos/{self.owner}/{self.repository}/issues/{issue_number}/comments",
        json={
            "body": body,
        },
    )
```

Isso permite que o agente registre automaticamente informações como:

```text
Implementação iniciada.

Implementação concluída.

Erro encontrado durante a implementação.

Issue movida para In Progress.

Issue validada e encerrada.
```

---

# 9. Adicionar Issue ao Project

Essa operação utiliza **GraphQL**.

Mutation:

```graphql
mutation AddIssueToProject(
  $projectId: ID!,
  $contentId: ID!
) {
  addProjectV2ItemById(
    input: {
      projectId: $projectId
      contentId: $contentId
    }
  ) {
    item {
      id
    }
  }
}
```

Variáveis:

```json
{
  "projectId": "PVT_xxxxx",
  "contentId": "I_kwDOxxxxx"
}
```

Implementação:

```python
def add_issue_to_project(
    self,
    issue_node_id: str,
    project_id: str,
):
    query = """
    mutation AddIssueToProject(
        $projectId: ID!,
        $contentId: ID!
    ) {
        addProjectV2ItemById(
            input: {
                projectId: $projectId
                contentId: $contentId
            }
        ) {
            item {
                id
            }
        }
    }
    """

    result = self.client.graphql_request(
        query,
        {
            "projectId": project_id,
            "contentId": issue_node_id,
        },
    )

    return result["addProjectV2ItemById"]["item"]
```

O retorno contém o ID do item dentro do Project:

```text
PVTI_xxxxxxxxx
```

Esse ID deve ser utilizado posteriormente para mover o card.

---

# 10. Encontrar as colunas do Kanban

No GitHub Projects atual, as colunas são normalmente representadas por opções do campo:

```text
Status
```

Exemplo:

```text
Status
├── Backlog
├── Todo
├── In Progress
└── Done
```

Portanto, a Tool deve:

1. Encontrar o campo `Status`
2. Obter suas opções
3. Encontrar a opção correspondente ao nome solicitado

## Query

```graphql
query GetProjectFields(
  $projectId: ID!
) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 100) {
        nodes {
          __typename

          ... on ProjectV2Field {
            id
            name
          }

          ... on ProjectV2SingleSelectField {
            id
            name

            options {
              id
              name
            }
          }
        }
      }
    }
  }
}
```

A Tool deverá localizar:

```text
name = "Status"
```

E obter algo semelhante a:

```json
{
  "id": "PVTSSF_xxxxx",
  "name": "Status",
  "options": [
    {
      "id": "abc",
      "name": "Backlog"
    },
    {
      "id": "def",
      "name": "Todo"
    },
    {
      "id": "ghi",
      "name": "In Progress"
    },
    {
      "id": "jkl",
      "name": "Done"
    }
  ]
}
```

---

# 11. Mover Issue entre colunas

Para mover uma Issue, devemos atualizar o campo `Status`.

Mutation:

```graphql
mutation MoveIssue(
  $projectId: ID!,
  $itemId: ID!,
  $fieldId: ID!,
  $optionId: String!
) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: {
        singleSelectOptionId: $optionId
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
```

Implementação:

```python
def move_issue(
    self,
    project_id: str,
    item_id: str,
    field_id: str,
    option_id: str,
):
    query = """
    mutation MoveIssue(
        $projectId: ID!,
        $itemId: ID!,
        $fieldId: ID!,
        $optionId: String!
    ) {
        updateProjectV2ItemFieldValue(
            input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: {
                    singleSelectOptionId: $optionId
                }
            }
        ) {
            projectV2Item {
                id
            }
        }
    }
    """

    return self.client.graphql_request(
        query,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )
```

---

# 12. Interface da Tool

A Tool pode expor as seguintes operações:

```python
create_issue(
    title,
    body=None,
    labels=None,
    assignees=None
)
```

```python
update_issue(
    issue_number,
    title=None,
    body=None,
    labels=None,
    assignees=None
)
```

```python
close_issue(
    issue_number,
    reason="completed"
)
```

```python
add_issue_to_project(
    issue_node_id,
    project_id
)
```

```python
move_issue(
    project_id,
    item_id,
    status
)
```

```python
add_comment(
    issue_number,
    body
)
```

---

# 13. Interface recomendada para um Agent

Se essa Tool for utilizada por um **LLM/Agent**, é melhor esconder os IDs internos do GitHub sempre que possível.

Em vez de exigir:

```python
move_issue(
    project_id="PVT_xxx",
    item_id="PVTI_xxx",
    field_id="PVTSSF_xxx",
    option_id="xxx"
)
```

preferir:

```python
move_issue(
    issue_number=123,
    status="In Progress"
)
```

Internamente a Tool faz:

```text
Issue #123
    │
    ├── descobrir node_id
    │
    ├── descobrir Project Item
    │
    ├── descobrir Status field
    │
    ├── descobrir option "In Progress"
    │
    └── atualizar campo
```

Isso deixa a Tool muito mais fácil para o Agent utilizar.

---

# 14. Fluxo completo de criação

Uma operação de alto nível pode ser:

```python
create_issue_and_add_to_project(
    title="Corrigir erro no login",
    body="O login retorna HTTP 500.",
    status="Todo"
)
```

Internamente:

```text
                Criar Issue
                     │
                     ▼
              Issue #123
                     │
                     ▼
          Adicionar ao Project
                     │
                     ▼
             Project Item
                     │
                     ▼
             Encontrar Status
                     │
                     ▼
                  "Todo"
                     │
                     ▼
              Atualizar campo
```

Resultado:

```text
Issue #123 criada
Issue adicionada ao Project
Status: Todo
```

---

# 15. Tratamento de erros

A Tool deve tratar pelo menos:

```text
401 → Token inválido
403 → Sem permissão
404 → Repository/Issue/Project não encontrado
422 → Dados inválidos
429 → Rate limit
```

Exemplo:

```python
try:
    result = self.client.rest_request(...)
except requests.HTTPError as error:
    response = error.response

    if response.status_code == 401:
        raise RuntimeError(
            "Token do GitHub inválido ou expirado."
        )

    if response.status_code == 403:
        raise RuntimeError(
            "Token sem permissão para executar esta operação."
        )

    if response.status_code == 404:
        raise RuntimeError(
            "Recurso do GitHub não encontrado."
        )

    raise
```

---

# 16. Boas práticas para a Tool

### Não expor o token

Nunca:

```python
github_token = "ghp_123456..."
```

Usar:

```python
os.getenv("GITHUB_TOKEN")
```

### Não depender de IDs fixos

Evitar:

```python
TODO_ID = "abc123"
```

Preferir descobrir:

```text
Status → options → "Todo" → ID
```

### Usar Issue Number para o usuário

Preferir:

```text
#123
```

em vez de exigir:

```text
I_kwDOxxxxxxxx
```

### Usar nomes para Status

Preferir:

```python
status="In Progress"
```

em vez de:

```python
option_id="PVTSSF_xxxxx"
```

---

# 17. Exemplo de fluxo completo do Agent

Uma interação poderia ser:

```text
Usuário:
"Crie uma issue para corrigir o problema do login,
adicione ao projeto e coloque em Todo."

Agent:
    ↓
create_issue()
    ↓
add_issue_to_project()
    ↓
move_issue(status="Todo")
    ↓
Resposta
```

Depois:

```text
Usuário:
"Comecei a trabalhar nessa issue."

Agent:
    ↓
move_issue(status="In Progress")
    ↓
add_comment("Implementação iniciada.")
```

E finalmente:

```text
Usuário:
"Terminei a implementação."

Agent:
    ↓
add_comment("Implementação concluída.")
    ↓
move_issue(status="Done")
    ↓
close_issue()
```

Resultado:

```text
┌─────────────────────────────────────────────┐
│ GitHub Project                              │
├──────────┬──────────┬────────────┬─────────┤
│ Backlog  │ Todo     │ In Progress│ Done    │
│          │          │            │         │
│          │          │            │ #123    │
│          │          │            │ Closed  │
└──────────┴──────────┴────────────┴─────────┘
```

---

# 18. Referências oficiais

- [GitHub REST API — Issues](https://docs.github.com/en/rest/issues/issues)
- [GitHub REST API — Issue Comments](https://docs.github.com/en/rest/issues/comments)
- [GitHub Projects API](https://docs.github.com/en/rest/projects)
- [GitHub — Using the API to manage Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)

## Resumo

O ponto principal para a implementação é:

```text
Issues
  → REST API

Projects
  → GraphQL API

Colunas do Kanban
  → opções do campo "Status"

Mover Issue
  → atualizar o valor do campo "Status"
```
