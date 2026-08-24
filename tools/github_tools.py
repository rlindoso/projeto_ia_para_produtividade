"""Ferramenta para administrar GitHub Issues e GitHub Projects (Projects v2)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
import subprocess
import json


class GithubTools:
    """Cliente de alto nível para Issues e Projects v2 do GitHub.

    As configurações podem ser informadas no construtor ou por variáveis de
    ambiente: ``GITHUB_TOKEN``, ``GITHUB_OWNER``, ``GITHUB_REPOSITORY`` e
    ``GITHUB_PROJECT_ID``.
    """

    REST_URL = "https://api.github.com"
    GRAPHQL_URL = f"{REST_URL}/graphql"
    API_VERSION = "2026-03-10"

    def __init__(
        self,
        github_token: str | None = None,
        owner: str | None = None,
        repository: str | None = None,
        project_id: str | None = None,
    ) -> None:
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.owner = owner or os.getenv("GITHUB_OWNER")
        self.repository = repository or os.getenv("GITHUB_REPOSITORY")
        self.project_id = project_id or os.getenv("GITHUB_PROJECT_ID")
        if not self.github_token:
            raise ValueError("A variável GITHUB_TOKEN não foi configurada.")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": self.API_VERSION,
        }

    def _gh(self, *args: str) -> str:
        env = os.environ.copy()

        # O gh deve utilizar a autenticação própria dele,
        # e não o Fine-grained PAT usado pela REST API.
        env.pop("GH_TOKEN", None)
        env.pop("GITHUB_TOKEN", None)

        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode != 0:
            details = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Sem detalhes."
            )

            raise RuntimeError(
                f"Erro ao executar gh {' '.join(args)}:\n{details}"
            )

        return result.stdout.strip()

    def _gh_json(self, *args: str) -> dict[str, Any]:
        output = self._gh(*args)

        if not output:
            return {}

        try:
            return json.loads(output)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"O gh não retornou JSON válido:\n{output}"
            ) from error
        
    def _repository_path(self, repository: str | None = None) -> str:
        repository = repository or self.repository
        if not repository:
            raise ValueError("A variável GITHUB_REPOSITORY não foi configurada.")
        if "/" in repository:
            return repository
        if not self.owner:
            raise ValueError("A variável GITHUB_OWNER não foi configurada.")
        return f"{self.owner}/{repository}"

    def _project_id(self, project_id: str | None = None) -> str:
        project_id = project_id or self.project_id
        if not project_id:
            raise ValueError("A variável GITHUB_PROJECT_ID não foi configurada.")
        return project_id

    @staticmethod
    def _raise_github_error(error: requests.HTTPError) -> None:
        response = error.response
        messages = {
            401: "Token do GitHub inválido ou expirado.",
            403: "Token sem permissão para executar esta operação.",
            404: "Recurso do GitHub não encontrado.",
            422: "Dados inválidos para a operação no GitHub.",
            429: "Limite de requisições do GitHub atingido.",
        }
        if response is not None and response.status_code in messages:
            raise RuntimeError(messages[response.status_code]) from error
        raise error

    def _rest_request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.REST_URL}{endpoint}",
                headers=self.headers,
                timeout=10,
                **kwargs,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            self._raise_github_error(error)
        if response.status_code == 204:
            return None
        return response.json()

    def _graphql_request(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                headers={**self.headers, "Content-Type": "application/json"},
                json={"query": query, "variables": variables or {}},
                timeout=10,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            self._raise_github_error(error)
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(f"Erro GraphQL do GitHub: {payload['errors']}")
        return payload["data"]

    def get_repo_info(self, repo_name: str | None = None) -> dict[str, Any]:
        """Consulta as informações de um repositório."""
        return self._rest_request("GET", f"/repos/{self._repository_path(repo_name)}")

    def get_issue(self, issue_number: int, repository: str | None = None) -> dict[str, Any]:
        """Consulta uma issue; o ``node_id`` retornado é usado nos Projects."""
        return self._rest_request(
            "GET", f"/repos/{self._repository_path(repository)}/issues/{issue_number}"
        )

    def find_issue_by_title(
        self,
        title: str,
        state: str = "open",
        repository: str | None = None,
    ) -> dict[str, Any] | None:
        """Busca uma issue aberta/fechada com título igual (ignorando maiúsculas)."""
        issues = self._rest_request(
            "GET",
            f"/repos/{self._repository_path(repository)}/issues",
            params={"state": state, "per_page": 100},
        )
        wanted = title.strip().casefold()
        for issue in issues:
            # O endpoint de issues também retorna pull requests.
            if "pull_request" in issue:
                continue
            if issue.get("title", "").strip().casefold() == wanted:
                return issue
        return None

    def create_issue(
        self,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        repository: str | None = None,
        skip_existing: bool = False,
    ) -> dict[str, Any]:
        """Cria uma issue e retorna os dados fornecidos pela API do GitHub.

        Com ``skip_existing=True``, se já existir uma issue (no estado
        informado) com o mesmo título, retorna-a sem criar outra, com a
        marcação ``"ja_existia": True`` no resultado.
        """
        if skip_existing:
            existing = self.find_issue_by_title(title, repository=repository)
            if existing:
                return {**existing, "ja_existia": True}
        payload: dict[str, Any] = {"title": title}
        if body is not None:
            payload["body"] = body
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        return self._rest_request(
            "POST", f"/repos/{self._repository_path(repository)}/issues", json=payload
        )

    def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        repository: str | None = None,
    ) -> dict[str, Any]:
        """Atualiza os campos informados de uma issue."""
        payload = {
            key: value
            for key, value in {
                "title": title,
                "body": body,
                "labels": labels,
                "assignees": assignees,
            }.items()
            if value is not None
        }
        if not payload:
            raise ValueError("Informe ao menos um campo para atualizar a issue.")
        return self._rest_request(
            "PATCH",
            f"/repos/{self._repository_path(repository)}/issues/{issue_number}",
            json=payload,
        )

    def close_issue(
        self,
        issue_number: int,
        reason: str = "completed",
        repository: str | None = None,
    ) -> dict[str, Any]:
        """Fecha uma issue com motivo ``completed`` ou ``not_planned``."""
        if reason not in {"completed", "not_planned"}:
            raise ValueError("O motivo deve ser 'completed' ou 'not_planned'.")
        return self._rest_request(
            "PATCH",
            f"/repos/{self._repository_path(repository)}/issues/{issue_number}",
            json={"state": "closed", "state_reason": reason},
        )

    def add_comment(
        self, issue_number: int, body: str, repository: str | None = None
    ) -> dict[str, Any]:
        """Adiciona um comentário a uma issue."""
        if not body.strip():
            raise ValueError("O comentário não pode estar vazio.")
        return self._rest_request(
            "POST",
            f"/repos/{self._repository_path(repository)}/issues/{issue_number}/comments",
            json={"body": body},
        )

    def add_issue_to_project(
        self,
        issue_number: int,
        project_number: int = 13,
        owner: str = "@me",
        repository: str | None = None,
    ) -> dict[str, Any]:

        repository_path = self._repository_path(repository)

        issue_url = (
            f"https://github.com/{repository_path}/issues/{issue_number}"
        )

        # Operação idempotente: se o card já existe, não duplica.
        try:
            self._get_project_item(
                issue_number=issue_number,
                project_number=project_number,
                owner=owner,
                repository=repository,
            )
        except RuntimeError:
            self._gh(
                "project",
                "item-add",
                str(project_number),
                "--owner",
                owner,
                "--url",
                issue_url,
            )

        return {
            "issue_number": issue_number,
            "issue_url": issue_url,
            "project_number": project_number,
        }

    def get_project_fields(
        self,
        project_number: int = 13,
        owner: str = "@me",
    ) -> list[dict[str, Any]]:
        result = self._gh_json(
            "project",
            "field-list",
            str(project_number),
            "--owner",
            owner,
            "--format",
            "json",
        )

        return result.get("fields", [])

    def _get_project_item(
        self,
        issue_number: int,
        project_number: int = 13,
        owner: str = "@me",
        repository: str | None = None,
    ) -> dict[str, Any]:

        items_result = self._gh_json(
            "project",
            "item-list",
            str(project_number),
            "--owner",
            owner,
            "--format",
            "json",
        )

        items = items_result.get("items", [])

        repository_path = self._repository_path(repository)

        issue_url = (
            f"https://github.com/{repository_path}/issues/{issue_number}"
        )

        for item in items:
            content = item.get("content") or {}

            if (
                content.get("number") == issue_number
                or content.get("url") == issue_url
            ):
                return item

        raise RuntimeError(
            f"A Issue #{issue_number} não está no Project #{project_number}."
        )

    def _get_status_option(
        self,
        status: str,
        project_number: int = 13,
        owner: str = "@me",
    ) -> dict[str, Any]:

        fields = self.get_project_fields(
            project_number,
            owner,
        )

        status_field = next(
            (
                field
                for field in fields
                if field.get("name", "").casefold() == "status"
            ),
            None,
        )

        if not status_field:
            raise RuntimeError(
                "Campo 'Status' não encontrado no Project."
            )

        options = status_field.get("options", [])

        option = next(
            (
                option
                for option in options
                if option.get("name", "").casefold()
                == status.casefold()
            ),
            None,
        )

        if not option:
            available = ", ".join(
                option.get("name", "")
                for option in options
            )

            raise ValueError(
                f"Status '{status}' não encontrado. "
                f"Disponíveis: {available}"
            )

        # return option
        return {
            "field_id": status_field["id"],
            "option_id": option["id"],
            "name": option["name"],
        }

    def move_issue(
        self,
        issue_number: int,
        status: str,
        project_number: int = 13,
        owner: str = "@me",
        repository: str | None = None,
    ) -> dict[str, Any]:

        item = self._get_project_item(
            issue_number=issue_number,
            project_number=project_number,
            owner=owner,
            repository=repository,
        )

        option = self._get_status_option(
            status=status,
            project_number=project_number,
            owner=owner,
        )

        item_id = item["id"]

        # Obtém o ID do Project.
        project = self._gh_json(
            "project",
            "view",
            str(project_number),
            "--owner",
            owner,
            "--format",
            "json",
        )

        project_id = project["id"]
        
        self._gh(
            "project",
            "item-edit",
            "--id",
            str(item_id),
            "--project-id",
            str(project_id),
            "--field-id",
            str(option["field_id"]),
            "--single-select-option-id",
            str(option["option_id"]),
        )

        return {
            "issue_number": issue_number,
            "item_id": item_id,
            "project_id": project_id,
            "status": option["name"],
            "status_id": option["option_id"],
        }

    def create_issue_and_add_to_project(
        self,
        title: str,
        body: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        repository: str | None = None,
        skip_existing: bool = True,
    ) -> dict[str, Any]:
        """Cria uma issue, adiciona-a ao Project e, opcionalmente, define o status.

        Por padrão (``skip_existing=True``), se já existir issue com o mesmo
        título, reutiliza-a em vez de criar duplicata.
        """
        issue = self.create_issue(
            title,
            body,
            labels,
            assignees,
            repository,
            skip_existing=skip_existing,
        )

        item = self.add_issue_to_project(
            issue_number=issue["number"],
            project_number=13,
            owner="@me",
            repository=repository,
        )
        result: dict[str, Any] = {"issue": issue, "project_item": item}
        if status is not None:
            result["move"] = self.move_issue(
                issue["number"], status, repository=repository
            )
        return result
