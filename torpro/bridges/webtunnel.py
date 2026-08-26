"""WebTunnel pluggable transport configuration strategy.

WebTunnel mimics standard HTTPS web browsing traffic to bypass Deep Packet Inspection.
"""

from typing import List, Optional

from torpro.bridges.base import BaseBridgeStrategy
from torpro.core.constants import CUSTOM_BRIDGES_FILE


class WebTunnelStrategy(BaseBridgeStrategy):
    """Generates WebTunnel pluggable transport configuration."""

    def __init__(self, custom_bridges: Optional[List[str]] = None) -> None:
        self._custom_bridges = custom_bridges or []

    @property
    def name(self) -> str:
        return "webtunnel"

    @property
    def description(self) -> str:
        return "WebTunnel (HTTPS traffic imitation, highly resilient to Deep Packet Inspection)"

    def _load_bridges(self) -> List[str]:
        """Load webtunnel bridge lines."""
        if self._custom_bridges:
            return self._custom_bridges

        bridges: List[str] = []
        if CUSTOM_BRIDGES_FILE.exists():
            content = CUSTOM_BRIDGES_FILE.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "webtunnel" in line:
                    if not line.startswith("Bridge "):
                        line = f"Bridge {line}"
                    bridges.append(line)
        return bridges

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for WebTunnel."""
        bridges = self._load_bridges()

        lines = [
            "# === WebTunnel Pluggable Transport Configuration ===",
            "UseBridges 1",
            "ClientTransportPlugin webtunnel exec ./bin/lyrebird",
            "",
        ]

        if bridges:
            lines.extend(bridges)
        else:
            lines.append("# [NOTE] Add WebTunnel bridge lines to config/custom_bridges.txt")

        return lines
