"""Tor IP Rotator and Circuit Renewal Service (SIGNAL NEWNYM).

Provides one-shot and continuous automated IP rotation by communicating
with Tor's ControlPort to request new identity circuits.
"""

from dataclasses import dataclass
from datetime import datetime
import socket
import time
from typing import Callable, Optional, Tuple

from torpro.core.constants import (
    AnsiColor,
    CONTROL_HOST,
    CONTROL_PORT,
)
from torpro.core.exceptions import ProcessError
from torpro.core.logger import Logger
from torpro.service.connection_tester import ConnectionTester


@dataclass
class RotationResult:
    """Outcome of a Tor IP rotation request."""
    success: bool
    new_ip: Optional[str] = None
    country: Optional[str] = None
    timestamp: str = ""
    message: str = ""


class TorIpRotator:
    """Manages Tor circuit renewal and IP rotation via ControlPort."""

    @classmethod
    def send_newnym(
        cls,
        host: str = CONTROL_HOST,
        port: int = CONTROL_PORT,
        password: str = "",
        timeout: float = 5.0,
    ) -> bool:
        """Send SIGNAL NEWNYM to Tor ControlPort to switch circuits."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))

            # 1. Authenticate with ControlPort
            auth_cmd = f'AUTHENTICATE "{password}"\r\n' if password else 'AUTHENTICATE ""\r\n'
            sock.sendall(auth_cmd.encode("utf-8"))
            resp = sock.recv(1024).decode("utf-8", errors="ignore")
            if not resp.startswith("250"):
                sock.close()
                Logger.error("Tor ControlPort authentication failed", resp.strip())
                return False

            # 2. Send SIGNAL NEWNYM
            sock.sendall(b"SIGNAL NEWNYM\r\n")
            resp = sock.recv(1024).decode("utf-8", errors="ignore")
            sock.close()

            if resp.startswith("250"):
                return True
            Logger.error("Tor rejected SIGNAL NEWNYM command", resp.strip())
            return False

        except (socket.timeout, ConnectionRefusedError, OSError) as err:
            Logger.error(
                f"Cannot connect to Tor ControlPort ({host}:{port})",
                f"Is Tor running with ControlPort enabled? ({err})",
            )
            return False

    @classmethod
    def rotate_now(cls, cooldown: float = 2.0) -> RotationResult:
        """Request new IP circuit and verify the new exit IP."""
        now_str = datetime.now().strftime("%H:%M:%S")
        if not cls.send_newnym():
            return RotationResult(
                success=False,
                timestamp=now_str,
                message="Failed to send NEWNYM signal to Tor ControlPort.",
            )

        # Allow Tor network to establish new circuit
        time.sleep(cooldown)

        # Verify new IP
        report = ConnectionTester.test_tor_connection()
        if report.is_connected and report.exit_ip:
            return RotationResult(
                success=True,
                new_ip=report.exit_ip,
                country=report.country or "Tor Exit Node",
                timestamp=now_str,
                message=f"IP changed successfully to {report.exit_ip}",
            )

        return RotationResult(
            success=True,
            new_ip="Rotating...",
            country="Tor Circuit",
            timestamp=now_str,
            message="NEWNYM signal accepted (IP will reflect on next outgoing request).",
        )

    @classmethod
    def run_auto_rotator(
        cls,
        interval_seconds: int = 30,
        on_rotate: Optional[Callable[[RotationResult], None]] = None,
    ) -> None:
        """Continuously rotate Tor IP every interval_seconds until interrupted."""
        Logger.header(f"Tor Pro Auto IP Rotator (Interval: {interval_seconds}s)")
        print(f"{AnsiColor.BOLD}Press Ctrl+C to stop auto IP rotation.{AnsiColor.RESET}\n")

        counter = 1
        try:
            while True:
                res = cls.rotate_now(cooldown=2.0)
                if on_rotate:
                    on_rotate(res)
                else:
                    if res.success and res.new_ip:
                        print(
                            f" [{res.timestamp}] {AnsiColor.BRIGHT_GREEN}[ROTATION #{counter}]{AnsiColor.RESET} "
                            f"{AnsiColor.BOLD}New IP:{AnsiColor.RESET} {AnsiColor.BRIGHT_CYAN}{res.new_ip:<16}{AnsiColor.RESET} "
                            f"| {AnsiColor.DIM}Country: {res.country}{AnsiColor.RESET}"
                        )
                    else:
                        print(f" [{res.timestamp}] {AnsiColor.BRIGHT_RED}[FAIL]{AnsiColor.RESET} {res.message}")

                counter += 1
                time.sleep(max(1, interval_seconds - 2))

        except KeyboardInterrupt:
            print(f"\n\n{AnsiColor.DIM}Auto IP rotation stopped by user.{AnsiColor.RESET}")
