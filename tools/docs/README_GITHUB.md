# Configuração do GitHub

Este projeto usa a classe `GithubTools`, em `tools/tools.py`, para criar e administrar Issues e incluí-las em um **GitHub Project (Projects v2)**. Issues e comentários usam a API REST; a inclusão e a movimentação no quadro usam a API GraphQL.

## Pré-requisitos

- Uma conta do GitHub com permissão de escrita no repositório.
- Um repositório no qual as Issues serão criadas.
- Um Project v2 pertencente ao usuário ou à organização.
- O [GitHub CLI (`gh`)](https://cli.github.com/), usado para consultar o ID do Project.
- Python 3 e as dependências do projeto:

  ```bash
  python3 -m pip install -r requirements.txt
  ```

`gh` é um programa de sistema, não uma dependência Python; portanto, ele não é incluído no `requirements.txt`.

## 0. Instalar e autenticar o GitHub CLI

Instale o `gh` conforme seu sistema operacional:

```bash
# macOS (Homebrew)
brew install gh

# Ubuntu/Debian
sudo apt update
sudo apt install gh

# Windows (PowerShell com winget)
winget install --id GitHub.cli
```

Confira a instalação e autentique a conta que tem acesso ao repositório e ao Project:

```bash
gh --version
gh auth login
gh auth status
```

No fluxo interativo de `gh auth login`, escolha `GitHub.com`, autenticação via navegador e a conta correta. Alternativamente, quando `GITHUB_TOKEN` já está exportado, o `gh` pode usá-lo diretamente; isso é útil para o comando GraphQL que obtém o ID do Project.

Para outras distribuições Linux e métodos de instalação, consulte as [instruções oficiais do GitHub CLI](https://cli.github.com/).

## 1. Criar e configurar o Project

1. No GitHub, abra o perfil ou a organização que será dona do quadro.
2. Acesse a aba **Projects** e clique em **New project**.
3. Escolha o template **Board** (ou crie um projeto vazio) e dê um nome ao quadro.
4. Confirme que há um campo de seleção única chamado exatamente `Status`. Crie-o caso necessário.
5. Adicione as opções que o agente deverá usar, por exemplo: `Backlog`, `Todo`, `In Progress` e `Done`.
6. Garanta que a conta associada ao token tenha permissão de escrita no Project. Em uma organização, isso pode exigir que um proprietário ou administrador a adicione ao Project.

O nome do campo deve ser `Status`: é assim que a tool localiza o campo. Os nomes das opções são livres, mas devem ser os mesmos passados para `move_issue(..., status="...")`.

## 2. Criar um token de acesso

Prefira um **fine-grained personal access token**, limitado ao repositório que será usado. Na tela de criação do token:

1. Escolha como *Resource owner* a conta ou organização dona dos recursos.
2. Em *Repository access*, selecione somente o repositório necessário.
3. Em *Repository permissions*, defina **Issues: Read and write**.
4. Se o Project pertence a uma organização, em *Organization permissions* defina **Projects: Read and write**.
5. Defina uma expiração curta apropriada, gere o token e guarde-o em local seguro. O GitHub só o mostra uma vez.

Para um Project pessoal, o token precisa pertencer a uma conta com escrita no Project. Para Projects de organização, políticas internas podem exigir a aprovação de um administrador antes de o token acessar recursos privados.

Se sua organização ainda utiliza tokens clássicos, use um token com o menor escopo possível que permita acesso ao repositório e a Projects; considere migrar para tokens refinados quando disponível.

## 3. Obter o ID do Project

`GITHUB_PROJECT_ID` não é o número visível na URL: ele é o **node ID** do Project, geralmente iniciado por `PVT_`.

Com o [GitHub CLI](https://cli.github.com/) autenticado, use um dos comandos abaixo. Substitua `DONO` pelo usuário ou organização e `NUMERO` pelo número do Project na URL, por exemplo, `3` em `/projects/3`.

Project de organização:

```bash
gh api graphql -f query='query($login: String!, $number: Int!) {
  organization(login: $login) { projectV2(number: $number) { id title } }
}' -f login='DONO' -F number=NUMERO
```

Project pessoal:

```bash
gh api graphql -f query='query($login: String!, $number: Int!) {
  user(login: $login) { projectV2(number: $number) { id title } }
}' -f login='DONO' -F number=NUMERO
```

Copie o valor retornado em `id` para `GITHUB_PROJECT_ID`.

## 4. Configurar o ambiente local

Copie o exemplo e preencha os valores reais:

```bash
cp .env.example .env
```

```env
GITHUB_TOKEN=github_pat_seu_token
GITHUB_OWNER=minha-organizacao
GITHUB_REPOSITORY=meu-repositorio
GITHUB_PROJECT_ID=PVT_seu_project_id
```

`GITHUB_OWNER` é o usuário ou organização do repositório, e `GITHUB_REPOSITORY` é somente o nome do repositório, sem `owner/`.

### Exemplo: `rlindoso/projeto_ia_para_produtividade`

Para usar a tool neste repositório, o arquivo `.env` fica assim. Substitua
apenas o token e o ID pelo valor do seu Project v2:

```env
GITHUB_TOKEN=github_pat_seu_token
GITHUB_OWNER=rlindoso
GITHUB_REPOSITORY=projeto_ia_para_produtividade
GITHUB_PROJECT_ID=PVT_13
```

Se o número do Project do usuário `rlindoso` for, por exemplo, `1`, obtenha o
ID com:

```bash
gh api graphql -f query='query($login: String!, $number: Int!) {
  user(login: $login) { projectV2(number: $number) { id title } }
}' -f login='rlindoso' -F number=1
```

Após exportar as variáveis, este exemplo cria uma Issue, inclui o card no
Project e o move para `Todo`:

```python
from tools.tools import GithubTools

github = GithubTools()
resultado = github.create_issue_and_add_to_project(
    title="Documentar a configuração da tool do GitHub",
    body="Adicionar instruções de uso e validação da integração.",
    status="Todo",
    labels=["documentation"],
)

print(resultado["issue"]["html_url"])
```

A classe carrega automaticamente o arquivo `.env` localizado na raiz do projeto. As variáveis já exportadas no sistema têm precedência sobre os valores desse arquivo.

Nunca versione o arquivo `.env` nem publique `GITHUB_TOKEN` em logs, notebooks ou mensagens.

## 5. Testar a configuração

Depois de salvar o `.env`, faça uma consulta que não altera dados:

```bash
python3 -c 'from tools.tools import GithubTools; print(GithubTools().get_repo_info()["full_name"])'
```

O comando deve mostrar `owner/repositorio`. A partir daí, operações como `create_issue_and_add_to_project(...)` criam a Issue, adicionam-na ao Project e definem o `Status` solicitado.

## Solução de problemas

| Mensagem ou status | Causa provável | Ação |
| --- | --- | --- |
| `401` | Token inválido, expirado ou não exportado. | Gere outro token e confira `GITHUB_TOKEN`. |
| `403` | Permissão insuficiente, política da organização ou limite de API. | Revise **Issues** e **Projects**, e peça aprovação do token se exigida. |
| `404` | Dono, repositório, Issue ou Project ID incorreto; também pode indicar recurso privado sem acesso. | Confira as variáveis e a permissão da conta. |
| `422` | Status, dados da Issue ou operação inválida. | Verifique o campo `Status` e suas opções no Project. |

## Referências

- [Gerenciar Projects com a API](https://docs.github.com/pt/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [Permissões para tokens refinados](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)
- [Gerenciar tokens de acesso pessoal](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
