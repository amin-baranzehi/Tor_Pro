"""Snowflake pluggable transport configuration strategy optimized for Iran.

Snowflake routes traffic through ephemeral WebRTC browser proxies.
STUN servers and Domain Fronting brokers are tailored for Iranian ISPs.
"""

from typing import List

from torpro.bridges.base import BaseBridgeStrategy
from torpro.core.constants import SNOWFLAKE_BIN


class SnowflakeStrategy(BaseBridgeStrategy):
    """Generates Snowflake configuration optimized for Iran filtering bypass."""

    # Responsive STUN servers in Iran (excluding blocked Google STUN)
    DEFAULT_STUN_SERVERS = [
        "stun:stun.antisip.com:3478",
        "stun:stun.dus.net:3478",
        "stun:stun.voip.blackberry.com:3478",
        "stun:stun.sonetel.com:3478",
        "stun:stun.uls.co.za:3478",
        "stun:stun.epygi.com:3478",
        "stun:stun.voys.nl:3478",
    ]

    # Azure Edge CDN fronting (Fastest & Most reliable in Iran)
    BROKER_URL = "https://snowflake-broker.azureedge.net/"
    FRONT_DOMAIN = "ajax.aspnetcdn.com"
    AMP_CACHE = "https://cdn.ampproject.org/"

    # Official Snowflake bridge lines
    SNOWFLAKE_BRIDGES = [
        "Bridge snowflake 192.0.2.3:1 2B280B23E1107BB62B76035334DAE028D75DD38B",
        "Bridge snowflake 192.0.2.4:2 8838EA4445A2D05A514DED231CD22F359A7684BD",
        "Bridge snowflake 192.0.2.5:3 8838EA4445A2D05A514DED231CD22F359A7684BD",
    ]

    @property
    def name(self) -> str:
        return "snowflake"

    @property
    def description(self) -> str:
        return "Snowflake (Azure CDN Front & Iran-Tested STUN Servers)"

    def generate_config_lines(self) -> List[str]:
        """Produce torrc lines for Snowflake optimized for Iran."""
        ice_servers = ",".join(self.DEFAULT_STUN_SERVERS)
        plugin_exec = (
            f"ClientTransportPlugin snowflake exec {SNOWFLAKE_BIN.as_posix()} "
            f"-url {self.BROKER_URL} "
            f"-front {self.FRONT_DOMAIN} "
            f"-ampcache {self.AMP_CACHE} "
            f"-ice {ice_servers}"
        )

        lines = [
            "# === Snowflake Pluggable Transport Configuration (Iran Optimized) ===",
            "UseBridges 1",
            plugin_exec,
            "",
        ]
        lines.extend(self.SNOWFLAKE_BRIDGES)
        return lines
