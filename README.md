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

# 📦 Estrutura do projeto

```text
projeto_ia_para_produtividade/
│
├── agents/
│   ├── agente_transcricao/
│   ├── agente_tasks/
│   ├── agente_github/
│   └── agente_slack/
│
├── prompts/
│   ├── ...
│
├── tools/
│   ├── github_tools.py
│   ├── ...
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

> A estrutura pode evoluir conforme os agentes forem implementados.

---

# 🛠️ Tecnologias

- 🐍 Python
- 🤖 LLM / agentes de IA
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
GITHUB_TOKEN=github_pat_xxxxxxxxx
GITHUB_OWNER=rlindoso
GITHUB_REPOSITORY=projeto_ia_para_produtividade
GITHUB_PROJECT_ID=PVT_xxxxxxxxx
```

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

Verifique o GitHub CLI:

```bash
gh --version
```

Autentique:

```bash
gh auth login
```

Depois execute o pipeline conforme o agente/orquestrador implementado.

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

- [ ] Implementar agente de transcrição.
- [ ] Estruturar saída do agente de contexto.
- [ ] Implementar agente de criação de tasks.
- [ ] Definir categorias e prioridades.
- [ ] Integrar agente de tasks com o GitHub.
- [ ] Automatizar criação e organização das Issues.
- [ ] Integrar comunicação com Slack.
- [ ] Criar um agente/orquestrador do pipeline.
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
