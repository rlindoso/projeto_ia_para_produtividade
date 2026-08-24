"""Ferramenta para enviar mensagens para o Slack via Web API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


class SlackTools:
    """Cliente de alto nível para operações de envio de mensagens no Slack.

    A configuração pode ser informada no construtor ou pelas variáveis de
    ambiente ``SLACK_BOT_TOKEN`` e ``SLACK_DEFAULT_CHANNEL_ID``.
    """

    API_URL = "https://slack.com/api"

    def __init__(
        self,
        slack_token: str | None = None,
        default_channel: str | None = None,
    ) -> None:
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")

        self.slack_token = slack_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel or os.getenv(
            "SLACK_DEFAULT_CHANNEL_ID"
        )

        if not self.slack_token:
            raise ValueError("A variável SLACK_BOT_TOKEN não foi configurada.")

        self.headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def send_message(
        self, channel: str | None, message: str
    ) -> dict[str, Any]:
        """Envia uma mensagem para um canal do Slack.

        Args:
            channel: ID do canal do Slack, por exemplo ``C0123456789``.
                Quando ``None``, usa o canal padrão configurado em
                ``SLACK_DEFAULT_CHANNEL_ID``.
            message: Texto da mensagem que será enviada.

        Returns:
            Dados retornados pela API do Slack.

        Raises:
            ValueError: Se o canal ou a mensagem estiverem vazios.
            RuntimeError: Se a API do Slack rejeitar a operação.
        """
        channel = channel or self.default_channel

        if not channel or not channel.strip():
            raise ValueError(
                "Informe o canal ou configure SLACK_DEFAULT_CHANNEL_ID."
            )

        if not message.strip():
            raise ValueError("A mensagem não pode estar vazia.")

        payload = {
            "channel": channel,
            "text": message,
        }

        try:
            response = requests.post(
                f"{self.API_URL}/chat.postMessage",
                headers=self.headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"Erro ao enviar mensagem para o Slack: {error}"
            ) from error

        result = response.json()

        if not result.get("ok"):
            error_code = result.get("error", "erro_desconhecido")
            raise RuntimeError(
                f"Erro da API do Slack ao enviar mensagem: {error_code}"
            )

        return result
