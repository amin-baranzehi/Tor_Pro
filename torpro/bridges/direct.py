"""Direct connection strategy without bridges."""

from typing import List

from torpro.bridges.base import BaseBridgeStrategy


class DirectStrategy(BaseBridgeStrategy):
    """Generates standard Tor configuration without bridges."""

    @property
    def name(self) -> str:
        return "direct"

    @property
    def description(self) -> str:
        return "Direct (Direct connection to Tor network without bridges)"

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for direct connection."""
        return [
            "# === Direct Connection (No Bridges) ===",
            "UseBridges 0",
        ]
