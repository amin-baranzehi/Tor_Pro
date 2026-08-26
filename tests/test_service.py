"""Unit tests for TorService and TorIpRotator."""

import unittest
from unittest.mock import MagicMock, patch

from torpro.service.ip_rotator import RotationResult, TorIpRotator
from torpro.service.tor_service import BootstrapStatus, TorService


class TestServiceSuite(unittest.TestCase):
    """Test suite for service controllers and IP rotator."""

    def test_bootstrap_parser(self):
        """Test parsing of Tor bootstrap log lines."""
        line = "Aug 26 19:48:49.000 [notice] Bootstrapped 80% (conn_or): Connecting to the Tor network"
        match = TorService.BOOTSTRAP_REGEX.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 80)
        self.assertEqual(match.group(2), "conn_or")

    def test_ip_rotator_rotation_result(self):
        """Test RotationResult data model."""
        res = RotationResult(success=True, new_ip="1.2.3.4", country="Germany")
        self.assertTrue(res.success)
        self.assertEqual(res.new_ip, "1.2.3.4")

    @patch("socket.socket")
    def test_send_newnym_mock(self, mock_socket_class):
        """Test send_newnym protocol communication."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        # Mock responses: 250 OK for AUTHENTICATE, 250 OK for SIGNAL NEWNYM
        mock_sock.recv.side_effect = [b"250 OK\r\n", b"250 OK\r\n"]

        success = TorIpRotator.send_newnym()
        self.assertTrue(success)
        mock_sock.sendall.assert_any_call(b"SIGNAL NEWNYM\r\n")


if __name__ == "__main__":
    unittest.main()
