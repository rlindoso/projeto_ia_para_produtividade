"""Ferramenta para transcrever áudio e carregar conversas em texto."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TranscriptionTools:
    """Cliente de alto nível para transcrição de áudio e leitura de texto."""

    def __init__(self) -> None:
        load_dotenv(_PROJECT_ROOT / ".env")
        self._client: OpenAI | None = None

    def _openai(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def resolve_path(self, path: str) -> Path:
        """Resolve um caminho relativo à raiz do projeto e exige que o arquivo exista."""
        if not path or not path.strip():
            raise ValueError("Informe o caminho do arquivo.")

        candidate = Path(path.strip()).expanduser()
        if not candidate.is_absolute():
            candidate = _PROJECT_ROOT / candidate
        candidate = candidate.resolve()

        if not candidate.is_file():
            raise ValueError(f"Arquivo não encontrado: {candidate}")
        return candidate

    def transcribe_audio(self, path: str, language: str = "pt") -> str:
        """Transcreve um arquivo de áudio para texto via Whisper."""
        audio_path = self.resolve_path(path)
        with audio_path.open("rb") as audio_file:
            result = self._openai().audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language or "pt",
            )
        texto = (result.text or "").strip()
        if not texto:
            raise ValueError("A transcrição do áudio veio vazia.")
        return texto

    def load_text(self, path: str) -> str:
        """Lê um arquivo de texto ou transcrição do disco."""
        text_path = self.resolve_path(path)
        texto = text_path.read_text(encoding="utf-8").strip()
        if not texto:
            raise ValueError(f"O arquivo está vazio: {text_path}")
        return texto
