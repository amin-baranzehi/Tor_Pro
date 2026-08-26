"""Bridge circumvention strategies package."""

from torpro.bridges.base import BaseBridgeStrategy
from torpro.bridges.direct import DirectStrategy
from torpro.bridges.fetcher import BridgeFetcher, FetchResult
from torpro.bridges.manager import BridgeManager
from torpro.bridges.obfs4 import Obfs4Strategy
from torpro.bridges.snowflake import SnowflakeStrategy
from torpro.bridges.webtunnel import WebTunnelStrategy

__all__ = [
    "BaseBridgeStrategy",
    "SnowflakeStrategy",
    "Obfs4Strategy",
    "WebTunnelStrategy",
    "DirectStrategy",
    "BridgeManager",
    "BridgeFetcher",
    "FetchResult",
]
