"""Unit tests for the bridge strategy patterns and configuration manager."""

from pathlib import Path
import unittest

from torpro.bridges.direct import DirectStrategy
from torpro.bridges.manager import BridgeManager
from torpro.bridges.obfs4 import Obfs4Strategy
from torpro.bridges.snowflake import SnowflakeStrategy
from torpro.bridges.webtunnel import WebTunnelStrategy
from torpro.core.constants import TORRC_PATH


class TestBridgeStrategies(unittest.TestCase):
    """Test suite for bridge strategies."""

    def test_snowflake_strategy(self):
        """Test Snowflake strategy generates valid configuration directives."""
        strategy = SnowflakeStrategy()
        lines = strategy.generate_config_lines()
        content = "\n".join(lines)
        self.assertIn("UseBridges 1", content)
        self.assertIn("snowflake-client", content)
        self.assertIn("Bridge snowflake", content)

    def test_obfs4_strategy(self):
        """Test Obfs4 strategy."""
        custom = ["Bridge obfs4 1.2.3.4:443 123456 cert=abc iat-mode=0"]
        strategy = Obfs4Strategy(custom_bridges=custom)
        lines = strategy.generate_config_lines()
        content = "\n".join(lines)
        self.assertIn("UseBridges 1", content)
        self.assertIn("ClientTransportPlugin obfs4", content)
        self.assertIn("1.2.3.4:443", content)

    def test_webtunnel_strategy(self):
        """Test WebTunnel strategy."""
        custom = ["Bridge webtunnel 1.2.3.4:443 123456 url=https://example.com/xyz"]
        strategy = WebTunnelStrategy(custom_bridges=custom)
        lines = strategy.generate_config_lines()
        content = "\n".join(lines)
        self.assertIn("UseBridges 1", content)
        self.assertIn("ClientTransportPlugin webtunnel", content)

    def test_direct_strategy(self):
        """Test Direct strategy."""
        strategy = DirectStrategy()
        lines = strategy.generate_config_lines()
        content = "\n".join(lines)
        self.assertIn("UseBridges 0", content)

    def test_bridge_manager_build_torrc(self):
        """Test BridgeManager assembly of active torrc file."""
        manager = BridgeManager()
        generated = manager.build_torrc(mode_name="snowflake")
        self.assertTrue(TORRC_PATH.exists())
        self.assertIn("SocksPort", generated)
        self.assertIn("snowflake", generated)


if __name__ == "__main__":
    unittest.main()
