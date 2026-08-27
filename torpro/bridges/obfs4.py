"""Obfs4 pluggable transport configuration strategy."""

from pathlib import Path
from typing import List, Optional

from torpro.bridges.base import BaseBridgeStrategy
from torpro.core.constants import CUSTOM_BRIDGES_FILE, LYREBIRD_BIN
from torpro.core.exceptions import ConfigError


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
                if line and not line.startswith("#") and "obfs4" in line:
                    if not line.startswith("Bridge "):
                        line = f"Bridge {line}"
                    bridges.append(line)
        return bridges

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for Obfs4."""
        bridges = self._load_bridges()

        if not bridges:
            raise ConfigError(
                "No Obfs4 bridge lines found in config/custom_bridges.txt!\n"
                "  -> To use Obfs4, please obtain fresh bridge lines (e.g. from https://bridges.torproject.org "
                "or Telegram @GetBridgesBot) and add them via Menu Option [7].\n"
                "  -> Alternatively, use Snowflake (Option [1]) which does not require static bridge lines."
            )

        lines = [
            "# === Obfs4 Pluggable Transport Configuration ===",
            "UseBridges 1",
            f"ClientTransportPlugin obfs4 exec {LYREBIRD_BIN.as_posix()}",
            "",
        ]
        lines.extend(bridges)
        return lines
