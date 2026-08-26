"""Tor connectivity verification and public IP inspector."""

from dataclasses import dataclass
import json
import socket
from typing import Optional, Tuple

from torpro.core.constants import (
    AnsiColor,
    HTTP_HOST,
    HTTP_PORT,
    SOCKS5_HOST,
    SOCKS5_PORT,
    TOR_CHECK_API_URL,
)
from torpro.core.logger import Logger
from torpro.core.process import CommandRunner


@dataclass
class ConnectionReport:
    """Outcome of a Tor connection test."""
    is_connected: bool
    is_tor: bool
    exit_ip: Optional[str]
    country: Optional[str]
    latency_ms: Optional[float]
    error_message: Optional[str] = None


class ConnectionTester:
    """Tests Tor proxy connectivity and retrieves exit node details."""

    @classmethod
    def test_socks_socket(cls, host: str = SOCKS5_HOST, port: int = SOCKS5_PORT) -> bool:
        """Check if SOCKS5 TCP port is accepting connections."""
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    @classmethod
    def test_http_socket(cls, host: str = HTTP_HOST, port: int = HTTP_PORT) -> bool:
        """Check if HTTP Bridge TCP port is accepting connections."""
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    @classmethod
    def test_tor_connection(cls) -> ConnectionReport:
        """Query Tor check API via SOCKS5/HTTP to determine Exit IP and Tor status."""
        if not cls.test_socks_socket():
            return ConnectionReport(
                is_connected=False,
                is_tor=False,
                exit_ip=None,
                country=None,
                latency_ms=None,
                error_message=f"Tor SOCKS5 port ({SOCKS5_HOST}:{SOCKS5_PORT}) is not reachable. Is Tor running?",
            )

        # Use curl with socks5-hostname if available
        res = CommandRunner.run(
            [
                "curl",
                "-s",
                "--connect-timeout",
                "10",
                "--socks5-hostname",
                f"{SOCKS5_HOST}:{SOCKS5_PORT}",
                TOR_CHECK_API_URL,
            ],
            timeout=15,
        )

        if res.is_success and res.stdout:
            try:
                data = json.loads(res.stdout)
                is_tor = data.get("IsTor", False)
                exit_ip = data.get("IP", "Unknown")
                return ConnectionReport(
                    is_connected=True,
                    is_tor=is_tor,
                    exit_ip=exit_ip,
                    country=data.get("Country", "Tor Network"),
                    latency_ms=None,
                )
            except json.JSONDecodeError:
                pass

        # Fallback: test via HTTP bridge
        if cls.test_http_socket():
            res_http = CommandRunner.run(
                [
                    "curl",
                    "-s",
                    "--connect-timeout",
                    "10",
                    "-x",
                    f"http://{HTTP_HOST}:{HTTP_PORT}",
                    TOR_CHECK_API_URL,
                ],
                timeout=15,
            )
            if res_http.is_success and res_http.stdout:
                try:
                    data = json.loads(res_http.stdout)
                    return ConnectionReport(
                        is_connected=True,
                        is_tor=data.get("IsTor", False),
                        exit_ip=data.get("IP", "Unknown"),
                        country=data.get("Country", "Tor Network"),
                        latency_ms=None,
                    )
                except Exception:
                    pass

        return ConnectionReport(
            is_connected=False,
            is_tor=False,
            exit_ip=None,
            country=None,
            latency_ms=None,
            error_message="Could not reach Tor Check API. Network might be slow or blocked.",
        )

    @classmethod
    def print_report(cls) -> None:
        """Run connectivity check and output report with standard ASCII banner."""
        Logger.print_banner()
        print(f"\n{AnsiColor.BOLD}{AnsiColor.BRIGHT_MAGENTA}--- Network Connection & IP Test ---{AnsiColor.RESET}\n")
        report = cls.test_tor_connection()

        if report.is_connected:
            tor_status = (
                f"{AnsiColor.BRIGHT_GREEN}YES (Connected to Tor Network){AnsiColor.RESET}"
                if report.is_tor
                else f"{AnsiColor.BRIGHT_YELLOW}Proxy active, but check API did not confirm Tor{AnsiColor.RESET}"
            )
            print(f" {AnsiColor.BOLD}* Connection Status:{AnsiColor.RESET} {AnsiColor.BRIGHT_GREEN}ONLINE{AnsiColor.RESET}")
            print(f" {AnsiColor.BOLD}* Tor Protected:{AnsiColor.RESET}     {tor_status}")
            print(f" {AnsiColor.BOLD}* Exit Node IP:{AnsiColor.RESET}      {AnsiColor.BRIGHT_CYAN}{report.exit_ip}{AnsiColor.RESET}")
            print(f" {AnsiColor.BOLD}* SOCKS5 Proxy:{AnsiColor.RESET}      {SOCKS5_HOST}:{SOCKS5_PORT}")
            print(f" {AnsiColor.BOLD}* HTTP/HTTPS Proxy:{AnsiColor.RESET}  {HTTP_HOST}:{HTTP_PORT}\n")
        else:
            print(f" {AnsiColor.BOLD}* Connection Status:{AnsiColor.RESET} {AnsiColor.BRIGHT_RED}OFFLINE / UNREACHABLE{AnsiColor.RESET}")
            if report.error_message:
                print(f"   {AnsiColor.DIM}-> Reason: {report.error_message}{AnsiColor.RESET}\n")
