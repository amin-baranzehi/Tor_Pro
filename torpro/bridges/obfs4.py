"""Obfs4 pluggable transport configuration strategy."""

from pathlib import Path
from typing import List, Optional

from torpro.bridges.base import BaseBridgeStrategy
from torpro.core.constants import CUSTOM_BRIDGES_FILE


class Obfs4Strategy(BaseBridgeStrategy):
    """Generates Obfs4 pluggable transport configuration."""

    def __init__(self, custom_bridges: Optional[List[str]] = None) -> None:
        self._custom_bridges = custom_bridges or []

    @property
    def name(self) -> str:
        return "obfs4"

    @property
    def description(self) -> str:
        return "Obfs4 (Obfuscated bridges with custom keys and ports)"

    def _load_bridges(self) -> List[str]:
        """Load bridges from parameter or custom_bridges.txt."""
        if self._custom_bridges:
            return self._custom_bridges

        bridges: List[str] = []
        if CUSTOM_BRIDGES_FILE.exists():
            content = CUSTOM_BRIDGES_FILE.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    if not line.startswith("Bridge "):
                        line = f"Bridge {line}"
                    bridges.append(line)
        return bridges

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for Obfs4."""
        bridges = self._load_bridges()

        lines = [
            "# === Obfs4 Pluggable Transport Configuration ===",
            "UseBridges 1",
            "ClientTransportPlugin obfs4 exec ./bin/lyrebird",
            "",
        ]

        if bridges:
            lines.extend(bridges)
        else:
            lines.append("# [WARNING] No obfs4 bridges specified in config/custom_bridges.txt")

        return lines
