"""Bridge Manager to coordinate strategies, base configurations, and active torrc.

Follows Factory and Strategy patterns for assembling clean Tor configuration files.
"""

from pathlib import Path
from typing import Dict, List, Optional

from torpro.bridges.base import BaseBridgeStrategy
from torpro.bridges.direct import DirectStrategy
from torpro.bridges.obfs4 import Obfs4Strategy
from torpro.bridges.snowflake import SnowflakeStrategy
from torpro.bridges.webtunnel import WebTunnelStrategy
from torpro.core.constants import (
    BASE_DIR,
    CONFIG_DIR,
    CONTROL_PORT,
    CUSTOM_BRIDGES_FILE,
    DATA_DIR,
    LOGS_DIR,
    SOCKS5_PORT,
    TOR_LOG_FILE,
    TOR_PID_FILE,
    TORRC_BASE,
    TORRC_PATH,
)
from torpro.core.exceptions import ConfigError
from torpro.core.logger import Logger


class BridgeManager:
    """Manages bridge strategies and active torrc generation."""

    def __init__(self) -> None:
        self._strategies: Dict[str, BaseBridgeStrategy] = {
            "snowflake": SnowflakeStrategy(),
            "obfs4": Obfs4Strategy(),
            "webtunnel": WebTunnelStrategy(),
            "direct": DirectStrategy(),
        }

    def get_strategies(self) -> Dict[str, BaseBridgeStrategy]:
        """Return registered strategies dict."""
        return self._strategies

    def get_strategy(self, mode_name: str) -> BaseBridgeStrategy:
        """Get strategy by name or raise ConfigError."""
        key = mode_name.lower().strip()
        if key not in self._strategies:
            valid_modes = ", ".join(self._strategies.keys())
            raise ConfigError(
                f"Unknown bridge mode '{mode_name}'. Available modes: {valid_modes}"
            )
        return self._strategies[key]

    @staticmethod
    def ensure_base_config() -> None:
        """Ensure config/torrc.base exists with robust portable defaults."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        default_base = (
            "# === Tor Pro Base Configuration ===\n"
            f"SocksPort {SOCKS5_PORT}\n"
            f"ControlPort {CONTROL_PORT}\n"
            f"DataDirectory {DATA_DIR.as_posix()}\n"
            f"PidFile {TOR_PID_FILE.as_posix()}\n"
            f"Log notice file {TOR_LOG_FILE.as_posix()}\n"
            "ClientOnly 1\n"
            "SafeLogging 0\n"
        )
        TORRC_BASE.write_text(default_base, encoding="utf-8")

    def build_torrc(self, mode_name: str = "snowflake", custom_bridges: Optional[List[str]] = None) -> str:
        """Generate combined torrc content and write to torrc file."""
        self.ensure_base_config()

        strategy = self.get_strategy(mode_name)
        if custom_bridges and hasattr(strategy, "_custom_bridges"):
            strategy._custom_bridges = custom_bridges

        base_content = TORRC_BASE.read_text(encoding="utf-8").strip()
        strategy_lines = strategy.generate_config_lines()

        full_config = (
            f"# ====================================================\n"
            f"# Tor Pro Active Configuration\n"
            f"# Active Mode: {strategy.name.upper()} ({strategy.description})\n"
            f"# Generated dynamically - Do not edit directly while running\n"
            f"# ====================================================\n\n"
            f"{base_content}\n\n"
            + "\n".join(strategy_lines)
            + "\n"
        )

        TORRC_PATH.write_text(full_config, encoding="utf-8")
        Logger.debug(f"Wrote active configuration for mode '{strategy.name}' to {TORRC_PATH}")
        return full_config

    @staticmethod
    def save_custom_bridges(bridge_lines: List[str]) -> None:
        """Save user-supplied bridge lines to config/custom_bridges.txt."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cleaned_lines = []
        for line in bridge_lines:
            line = line.strip()
            if line:
                if not line.startswith("Bridge ") and not line.startswith("#"):
                    line = f"Bridge {line}"
                cleaned_lines.append(line)

        CUSTOM_BRIDGES_FILE.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
        Logger.success(f"Saved {len(cleaned_lines)} bridge line(s) to {CUSTOM_BRIDGES_FILE.name}")
