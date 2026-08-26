"""Snowflake pluggable transport configuration strategy.

Snowflake routes traffic through ephemeral WebRTC browser proxies. It is highly
effective in heavily censored regions because it does not rely on static bridge IPs.
"""

from typing import List

from torpro.bridges.base import BaseBridgeStrategy
from torpro.core.constants import SNOWFLAKE_BIN


class SnowflakeStrategy(BaseBridgeStrategy):
    """Generates optimal Snowflake pluggable transport configuration."""

    # Reliable STUN servers for WebRTC NAT traversal
    DEFAULT_STUN_SERVERS = [
        "stun:stun.l.google.com:19302",
        "stun:stun.voip.blackberry.com:3478",
        "stun:stun.altariproductions.com:3478",
        "stun:stun.antisip.com:3478",
        "stun:stun.bluesip.net:3478",
        "stun:stun.dus.net:3478",
        "stun:stun.epygi.com:3478",
        "stun:stun.sonetel.com:3478",
        "stun:stun.uls.co.za:3478",
        "stun:stun.voipgate.com:3478",
        "stun:stun.voys.nl:3478",
    ]

    # Fastly broker URL and domain fronts
    BROKER_URL = "https://snowflake-broker.torproject.net.global.prod.fastly.net/"
    FRONT_DOMAIN = "cdn.sstatic.net"
    AMP_CACHE = "https://cdn.ampproject.org/"

    # Official Snowflake bridge lines
    SNOWFLAKE_BRIDGES = [
        "Bridge snowflake 192.0.2.3:1 2B280B23E1107BB62B76035334DAE028D75DD38B",
        "Bridge snowflake 192.0.2.4:2 8838EA4445A2D05A514DED231CD22F359A7684BD",
    ]

    @property
    def name(self) -> str:
        return "snowflake"

    @property
    def description(self) -> str:
        return "Snowflake (WebRTC ephemeral proxies, best for filtered networks without static IP)"

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for Snowflake."""
        ice_servers = ",".join(self.DEFAULT_STUN_SERVERS)
        plugin_exec = (
            f"ClientTransportPlugin snowflake exec ./bin/snowflake-client "
            f"-url {self.BROKER_URL} "
            f"-front {self.FRONT_DOMAIN} "
            f"-ampcache {self.AMP_CACHE} "
            f"-ice {ice_servers}"
        )

        lines = [
            "# === Snowflake Pluggable Transport Configuration ===",
            "UseBridges 1",
            plugin_exec,
            "",
        ]
        lines.extend(self.SNOWFLAKE_BRIDGES)
        return lines
