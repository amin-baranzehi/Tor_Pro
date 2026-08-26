"""Unit tests for the HTTP bridge and system proxy managers."""

import socket
import unittest

from torpro.core.constants import BASE_DIR, HTTP_PORT, SOCKS5_PORT
from torpro.proxy.http_bridge import HttpBridgeService
from torpro.proxy.sysproxy import SystemProxyManager


class TestProxySuite(unittest.TestCase):
    """Test suite for proxy utilities."""

    def test_env_script_generation(self):
        """Test generation of env.sh shell script."""
        script_path = SystemProxyManager.generate_env_script()
        self.assertTrue(script_path.exists())
        content = script_path.read_text(encoding="utf-8")
        self.assertIn(f"http://127.0.0.1:{HTTP_PORT}", content)
        self.assertIn(f"socks5h://127.0.0.1:{SOCKS5_PORT}", content)

    def test_http_bridge_state_methods(self):
        """Test HTTP Bridge PID detection logic."""
        is_running = HttpBridgeService.is_running()
        self.assertIsInstance(is_running, bool)


if __name__ == "__main__":
    unittest.main()
