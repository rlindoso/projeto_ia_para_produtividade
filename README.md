# 🤖 Projeto IA para Produtividade

> **Pipeline multi-agente para transformar conversas em tarefas organizadas e executáveis.**

Este projeto propõe um pipeline de **agentes especializados** capaz de receber uma conversa, áudio ou transcrição, identificar o que realmente importa, transformar os pontos relevantes em tarefas estruturadas e executar ações automaticamente no **GitHub** e no **Slack**.

```text
🎙️ Conversa
   ↓
📝 Transcrição e contexto
   ↓
🧠 Tópicos relevantes
   ↓
📋 Tasks estruturadas
   ↓
🐙 GitHub
   ↓
💬 Slack
```

---

## 🎯 Objetivo

Reduzir o trabalho manual necessário para transformar uma conversa de planejamento, reunião ou alinhamento em ações concretas.

Em vez de:

```text
Reunião
   ↓
Pessoa escuta novamente
   ↓
Anota tarefas
   ↓
Organiza as tarefas
   ↓
Cria Issues
   ↓
Coloca no Kanban
   ↓
Move as tarefas
   ↓
Avisa a equipe
```

o pipeline busca automatizar:

```text
Reunião / Áudio
       ↓
Agente de Transcrição
       ↓
Agente de Tasks
       ↓
Agente GitHub
       ↓
Agente Slack
```

---

# 🧩 Arquitetura

O sistema é dividido em **4 agentes especializados**:

```text
                    ┌─────────────────────┐
                    │      ENTRADA        │
                    │                     │
                    │ 🎙️ Áudio / Texto    │
                    │ 💬 Conversa         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  1. TRANSCRIÇÃO     │
                    │                     │
                    │ • Áudio → texto     │
                    │ • Divide tópicos    │
                    │ • Remove ruídos     │
                    │ • Mantém contexto   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   2. AGENTE TASKS   │
                    │                     │
                    │ • Analisa tópicos   │
                    │ • Cria tarefas      │
                    │ • Categoriza        │
                    │ • Estrutura saída   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   3. AGENTE GITHUB  │
                    │                     │
                    │ • Cria Issues       │
                    │ • Edita Issues      │
                    │ • Fecha Issues      │
                    │ • Project/Kanban    │
                    │ • Move Status       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    4. AGENTE SLACK  │
                    │                     │
                    │ • Comunicação       │
                    │ • Notificações      │
                    │ • Resumo das ações  │
                    └─────────────────────┘
```

---

# 🤖 Agentes

> **Status da implementação:** ✅ **Agente de Transcrição**, ✅ **Agente GitHub**, ✅ **Agente Slack** e ✅ **Agente Orquestrador** já implementados em `agents/`, seguindo o padrão LangGraph (`SYSTEM_AGENT_*` + tools). O Agente de Tasks representa a próxima etapa do pipeline.

## 1. 🎙️ Agente de Transcrição e Contexto

É a porta de entrada do pipeline.

### Responsabilidades

- Receber áudio ou texto.
- Converter áudio em texto.
- Dividir a conversa em tópicos.
- Identificar trechos relevantes.
- Remover informações que não fazem parte do contexto de trabalho.
- Preservar informações importantes para as próximas etapas.
- Entregar uma saída estruturada para o agente responsável pela criação das tasks.

### Exemplo

Entrada:

```text
"Bom dia pessoal, antes de começar queria comentar que hoje
está bastante calor...

Ah, sobre o projeto, precisamos corrigir o erro do login.
Também precisamos atualizar a documentação da API.
Depois vemos aquela ideia do dashboard..."
```

Saída:

```json
{
  "topics": [
    {
      "title": "Correção do login",
      "context": "Corrigir o erro que ocorre durante o login."
    },
    {
      "title": "Documentação da API",
      "context": "Atualizar a documentação da API."
    },
    {
      "title": "Dashboard",
      "context": "Avaliar posteriormente a ideia de criar um dashboard."
    }
  ]
}
```

---

# 2. 🧠 Agente de Tasks

Recebe os tópicos tratados pelo primeiro agente e transforma as informações em **tarefas acionáveis**.

### Responsabilidades

- Interpretar os tópicos.
- Identificar ações necessárias.
- Criar tarefas.
- Categorizar tarefas.
- Definir contexto.
- Identificar prioridade quando possível.
- Estruturar a saída para integração com o GitHub.

### Exemplo

Entrada:

```json
{
  "title": "Correção do login",
  "context": "Corrigir o erro que ocorre durante o login."
}
```

Saída:

```json
{
  "tasks": [
    {
      "title": "Corrigir erro no login",
      "description": "Investigar e corrigir o erro apresentado durante o login.",
      "category": "bug",
      "priority": "high"
    }
  ]
}
```

---

# 3. 🐙 Agente GitHub

É responsável por transformar as tasks em ações no GitHub.

### Responsabilidades

- Criar Issues.
- Editar Issues.
- Fechar Issues.
- Adicionar comentários.
- Adicionar Issues ao Project.
- Mover Issues entre os status do Kanban.
- Associar informações da task à Issue.
- Retornar o resultado das operações.

### Exemplo

```text
Task
  ↓
Criar Issue
  ↓
Adicionar ao Project
  ↓
Definir Status
  ↓
Retornar URL da Issue
```

Resultado:

```text
✅ Issue #123 criada
✅ Adicionada ao Project
✅ Status: Todo
```

### Integração

A arquitetura utiliza:

```text
GitHub REST API
        +
GitHub CLI (gh)
```

A REST API é utilizada para operações relacionadas às Issues, enquanto o `gh` é utilizado para operações do Project/Kanban.

---

# 4. 💬 Agente Slack

É responsável pela comunicação com os usuários/equipe.

### Responsabilidades

- Enviar mensagens.
- Notificar a criação de tarefas.
- Informar alterações no GitHub.
- Enviar resumos do processamento.
- Comunicar erros ou ações que precisam de intervenção humana.

### Exemplo

```text
🤖 Pipeline concluído!

Foram identificadas 3 tarefas na conversa:

🐛 Corrigir erro no login
📚 Atualizar documentação da API
📊 Avaliar criação do dashboard

GitHub:
✅ 3 Issues criadas
✅ Issues adicionadas ao Project

As tarefas estão disponíveis no Kanban.
```

---

# 🔄 Pipeline completo

```text
┌──────────────┐
│    Áudio     │
│      ou      │
│     Texto    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ 1. Agente Transcrição   │
│                         │
│ Áudio → Texto           │
│ Texto → Tópicos         │
│ Remove informações      │
│ fora do contexto        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Agente de Tasks      │
│                         │
│ Tópicos → Tasks         │
│                         │
│ • título                │
│ • descrição             │
│ • categoria             │
│ • prioridade            │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Agente GitHub        │
│                         │
│ Tasks → Issues          │
│                         │
│ • criar                 │
│ • adicionar ao Project  │
│ • mover no Kanban       │
│ • fechar                │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Agente Slack         │
│                         │
│ Resultado → Comunicação │
└─────────────────────────┘
```

---

# 🕸️ Implementação atual: Orquestrador + Agentes GitHub e Slack

A implementação segue o padrão: um grafo **LangGraph** que alterna entre o nó `agent` (modelo com tool calling) e o nó `tools` (execução das ferramentas) até a resposta final.

```text
Usuário
   ↓
Agente Orquestrador (grafo LangGraph)
   │  tools: [agente_transcricao, agente_github, agente_slack]
   │
   ├──► Agente Transcrição (grafo LangGraph)
   │       │  tools: [transcrever_audio, carregar_transcricao, estruturar_conversa]
   │       ▼
   │    TranscriptionTools (tools/transcription_tools.py)
   │       ├── Whisper     → áudio → texto
   │       └── arquivo     → texto da transcrição
   │
   ├──► Agente GitHub (grafo LangGraph)
   │       │  tools: [criar_issue, mover_no_kanban, ...]
   │       ▼
   │    GithubTools (tools/github_tools.py)
   │       ├── REST API    → Issues
   │       └── gh CLI      → Projects v2 / Kanban
   │
   └──► Agente Slack (grafo LangGraph)   ← chamado ao final, com o resumo
           │  tools: [enviar_mensagem]
           ▼
        SlackTools (tools/slack_tools.py)
           └── Slack Web API → chat.postMessage
```

### Componentes

| Arquivo | Responsabilidade |
|---|---|
| `agents/base.py` | `AgentState`, classe `Agent` (grafo), `load_chat_model()`, `extrair_parametros()` e `anunciar_ferramenta()` |
| `agents/schemas.py` | Modelos Pydantic para extração estruturada de parâmetros das tools |
| `agents/agent_transcricao.py` | Especialista em limpar conversas; expõe `TranscriptionTools` como `@tool`s e devolve o prompt para o próximo agente |
| `agents/agent_github.py` | Especialista em Issues/Projects; expõe `GithubTools` como `@tool`s |
| `agents/agent_slack.py` | Especialista em comunicação; expõe `SlackTools` como `@tool`s |
| `agents/agent_orchestrator.py` | Delega solicitações aos agentes especialistas registrados em `AGENTES_ORQUESTRADOS`; ao final de ações executadas, aciona o Agente Slack com o resumo |
| `tools/transcription_tools.py` | Cliente de alto nível da transcrição (Whisper + leitura de arquivos de texto) |
| `tools/github_tools.py` | Cliente de alto nível do GitHub (Issues via REST, Projects/Kanban via `gh`) |
| `tools/slack_tools.py` | Cliente de alto nível do Slack (Web API, canal padrão via `SLACK_DEFAULT_CHANNEL_ID`) |

### Extração estruturada de parâmetros

Cada tool recebe a mensagem em linguagem natural e extrai os parâmetros com uma classe Pydantic + `with_structured_output`, antes de chamar a API:

```python
params: MoverNoKanbanRequest = extrair_parametros(
    MoverNoKanbanRequest,
    "Extraia o número da issue e a coluna de destino no Kanban...",
    mensagem_usuario,
)
```

Se um parâmetro obrigatório não estiver na mensagem, o schema retorna `null` e a tool falha com erro explícito — nunca inventa valores.

### Idempotência

- `criar_issue` / `criar_issue_no_project` usam `skip_existing=True`: se já existe issue aberta com o mesmo título, reutilizam-na (retorno marcado com `"ja_existia": true`).
- `add_issue_to_project` só adiciona o card se a issue ainda não estiver no Project.

Isso evita issues e cards duplicados quando o agente repete chamadas.

### Como adicionar um novo especialista

1. Crie `agents/agent_<nome>.py` usando `Agent`/`load_chat_model()` de `agents/base.py`.
2. Envolva-o em uma `@tool` no orquestrador (como `agente_github`).
3. Registre a tool em `AGENTES_ORQUESTRADOS` (`agents/agent_orchestrator.py`).

---

# 📦 Estrutura do projeto

```text
projeto_ia_para_produtividade/
│
├── agents/
│   ├── __init__.py
│   ├── base.py                  # AgentState + classe Agent (grafo LangGraph)
│   ├── schemas.py               # Modelos Pydantic de extração de parâmetros
│   ├── agent_github.py          # ✅ Agente especialista em Issues/Projects
│   ├── agent_slack.py           # ✅ Agente especialista em comunicação no Slack
│   ├── agent_orchestrator.py    # ✅ Orquestra agentes especialistas como tools
│   └── agent_transcricao.py     # ✅ Limpa conversa e estrutura briefing para tasks
│
├── prompts/
│   └── README.md
│
├── tools/
│   ├── transcription_tools.py   # TranscriptionTools: Whisper + leitura de texto
│   ├── github_tools.py          # GithubTools: Issues (REST) + Projects (gh CLI)
│   ├── slack_tools.py           # SlackTools: Web API (chat.postMessage)
│   └── docs/                    # Guias de configuração das ferramentas
│
├── docs/
├── .env.example
├── requirements.txt
└── README.md
```

> A estrutura pode evoluir conforme os agentes forem implementados.

---

# 🛠️ Tecnologias

- 🐍 Python
- 🦜 LangChain + LangGraph (grafos de agentes)
- 🤖 OpenAI API (`gpt-4o-mini` por padrão)
- 🎙️ Transcrição de áudio
- 🐙 GitHub REST API
- 🐙 GitHub CLI (`gh`)
- 📋 GitHub Projects
- 💬 Slack API
- 🔐 Variáveis de ambiente

---

# 🔐 Configuração

Crie um arquivo `.env` baseado no `.env.example`.

Exemplo:

```env
OPENAI_API_KEY=sk_xxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

GITHUB_TOKEN=github_pat_xxxxxxxxx
GITHUB_OWNER=rlindoso
GITHUB_REPOSITORY=projeto_ia_para_produtividade
GITHUB_PROJECT_ID=PVT_xxxxxxxxx

SLACK_BOT_TOKEN=xoxb_xxxxxxxxx
SLACK_DEFAULT_CHANNEL_ID=C0BS9C37QRJ
```

`OPENAI_API_KEY` é usada pelo modelo dos agentes (`gpt-4o-mini` por padrão, configurável em `OPENAI_MODEL`).

O token utilizado pela API do GitHub deve possuir as permissões necessárias para as operações de Issues.

Para operações do Project realizadas pelo `gh`, a autenticação do GitHub CLI deve estar configurada separadamente:

```bash
gh auth login
gh auth status
```

---

# ▶️ Executando

Instale as dependências:

```bash
pip install -r requirements.txt
```

Verifique o GitHub CLI e autentique (necessário para o Kanban):

```bash
gh --version
gh auth login
```

Configure o `.env` conforme a seção anterior.

### Script interativo (recomendado)

Na raiz do projeto, execute sem parâmetros — o script mostra um resumo, carrega os agentes e pergunta o que deve ser feito:

```bash
python main.py
```

Digite o pedido e aguarde; a resposta final é impressa no terminal (com o rastreamento das ferramentas utilizadas). Enter vazio ou `Ctrl+C` encerra.

### Via linha de comando

Também é possível passar a solicitação diretamente ao orquestrador:

```bash
python -m agents.agent_orchestrator "Precisamos documentar a API. Crie essa tarefa no GitHub e coloque no Backlog do Kanban."
```

O orquestrador analisa a solicitação e delega ao especialista adequado:

Saída esperada (rastreamento das tools + resposta final):

```text
Ferramenta 'agente_github' chamada com os argumentos: {'solicitacao': '...'}
Ferramenta 'criar_issue_no_project' chamada com os argumentos: {'mensagem_usuario': '...'}
Ferramenta criar_issue_no_project utilizada com os parametros: {"title":"Documentar a API","status":"Backlog",...}
A tarefa foi criada: https://github.com/owner/repo/issues/12 ...
```

### Agente GitHub direto

Sem passar pelo orquestrador:

```bash
python -m agents.agent_github "Crie uma issue 'Revisar o README' e coloque em Todo."
python -m agents.agent_github "Consulte a issue #12"
```

### Agente de Transcrição direto

```bash
python -m agents.agent_transcricao "Estruture a transcrição em docs/transcricao_feature_teleconsulta.txt"
```

O agente carrega o texto, descarta o que não é o contexto principal, divide em tópicos e devolve o `prompt_for_task_agent` para o próximo especialista.

### Agente Slack direto

```bash
python -m agents.agent_slack "Avise a equipe que o deploy de hoje foi concluído."
```

Também é possível aceitar a pergunta pela linha de comando livremente — o texto após o módulo é repassado ao agente; sem argumentos, um exemplo padrão é executado.

### Uso programático

```python
from agents.agent_orchestrator import build_orchestrator
from agents.agent_github import build_agent
from agents.agent_transcricao import build_agent as build_transcricao

orquestrador = build_orchestrator()
resultado = orquestrador.invoke("Crie uma issue para revisar os testes e coloque no Kanban")
print(resultado["messages"][-1].content)

agente_transcricao = build_transcricao()
resultado = agente_transcricao.invoke(
    "Estruture a transcrição em docs/transcricao_feature_teleconsulta.txt"
)
print(resultado["messages"][-1].content)

agente_github = build_agent()
resultado = agente_github.invoke("Mova a issue #12 para In Progress")
print(resultado["messages"][-1].content)
```

---

# 🧱 Princípios da arquitetura

### Agentes especializados

Cada agente possui uma responsabilidade clara:

```text
Transcrição
    ↓
Contexto
    ↓
Tasks
    ↓
GitHub
    ↓
Slack
```

### Saídas estruturadas

Os agentes devem preferencialmente produzir dados estruturados entre etapas.

```json
{
  "tasks": [
    {
      "title": "Corrigir erro no login",
      "description": "Corrigir erro HTTP 500 durante autenticação.",
      "category": "bug",
      "priority": "high"
    }
  ]
}
```

### Separação entre raciocínio e ferramentas

O agente decide **o que precisa ser feito**.

As Tools executam **como fazer**.

```text
Agente
  │
  │ "Criar uma Issue"
  ▼
Tool GitHub
  │
  │ API / CLI
  ▼
GitHub
```

Essa separação facilita testes, manutenção e evolução do sistema.

---

# 🔮 Próximos passos

- [x] Implementar agente de transcrição.
- [x] Estruturar saída do agente de contexto.
- [ ] Implementar agente de criação de tasks.
- [ ] Definir categorias e prioridades.
- [ ] Integrar agente de tasks com o GitHub.
- [x] Automatizar criação e organização das Issues.
- [x] Integrar comunicação com Slack (agente especialista).
- [x] Criar um agente/orquestrador do pipeline.
- [ ] Adicionar tratamento de erros e retries.
- [ ] Adicionar logs e observabilidade.
- [ ] Criar testes automatizados para as Tools.
- [ ] Adicionar aprovação humana antes de ações destrutivas.
- [ ] Permitir processamento de múltiplas conversas.
- [ ] Criar histórico das execuções do pipeline.

---

# 🧪 Exemplo de execução

```text
Entrada
│
├── "Precisamos corrigir o login"
├── "Atualizar a documentação"
└── "Criar um dashboard"
        │
        ▼
Agente de Transcrição
        │
        ▼
3 tópicos relevantes
        │
        ▼
Agente de Tasks
        │
        ├── 🐛 Corrigir login
        ├── 📚 Atualizar documentação
        └── 📊 Criar dashboard
        │
        ▼
Agente GitHub
        │
        ├── Issue #101
        ├── Issue #102
        └── Issue #103
        │
        ▼
Agente Slack
        │
        ▼
"3 tarefas foram criadas no GitHub."
```

---

# 🎯 Visão do projeto

O objetivo final é transformar o projeto em um **assistente de produtividade orientado a agentes**, capaz de acompanhar o ciclo completo:

```text
                 CONVERSA
                    │
                    ▼
              COMPREENSÃO
                    │
                    ▼
               PLANEJAMENTO
                    │
                    ▼
                 EXECUÇÃO
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       GitHub               Slack
          │                   │
          ▼                   ▼
       Tasks               Pessoas
          │
          ▼
       Kanban
```

A IA deixa de atuar apenas como uma interface de perguntas e respostas e passa a atuar como uma **camada de automação entre comunicação, planejamento e execução**.

---

## 👥 Projeto

**Projeto IA para Produtividade**

Um estudo prático de **sistemas multi-agente, automação e integração de ferramentas de produtividade**.

---

## 📚 Links

- [Repositório GitHub](https://github.com/rlindoso/projeto_ia_para_produtividade)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub CLI](https://cli.github.com/)
- [Slack API](https://api.slack.com/)

---

> 🚀 **Da conversa à execução: menos trabalho operacional, mais produtividade.**
