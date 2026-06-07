"""Base profile contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProfile(ABC):
    """A profile owns one stage responsibility."""

    name: str = "base-profile"
    stage: str = "unknown"

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the profile and return context updates."""

