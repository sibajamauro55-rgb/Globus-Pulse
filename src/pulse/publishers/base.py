from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PublishResult:
    ok: bool
    platform: str
    adapter: str
    mode: str  # live | blocked
    external_id: str | None = None
    error: str | None = None


class Publisher(ABC):
    platform: str
    adapter: str

    @abstractmethod
    def ready(self) -> tuple[bool, str]:
        """True si hay credenciales/config para publicar de verdad."""

    @abstractmethod
    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        """Publicación real o bloqueo explícito. Nunca finge un published."""
