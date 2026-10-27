"""Runtime settings resolved from the sidebar (API key, model, mode)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.llm import GeminiClient


@dataclass(frozen=True)
class AppSettings:
    api_key: Optional[str]
    model: str

    @property
    def live(self) -> bool:
        return bool(self.api_key)

    @property
    def mode_label(self) -> str:
        return f"Live AI · {self.model}" if self.live else "Demonstration mode"

    def client(self) -> GeminiClient:
        """Create a Gemini client. Callers must check `live` first."""
        if not self.api_key:
            raise ValueError("No API key configured")
        return GeminiClient(self.api_key, self.model)
