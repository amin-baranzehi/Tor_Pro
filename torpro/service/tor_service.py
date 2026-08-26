"""Tor background service controller and bootstrap progress monitor.

Encapsulates process lifecycle, bootstrap parsing, log monitoring,
and coordinated startup/shutdown of Tor core + HTTP Bridge.
"""

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from typing import Callable, Generator, List, Optional, Tuple

from torpro.bridges.manager import BridgeManager
from torpro.core.constants import (
    BOOTSTRAP_TIMEOUT_SECONDS,
    DATA_DIR,
    LIB_DIR,
    LOGS_DIR,
    TOR_BIN,
    TOR_LOG_FILE,
    TOR_PID_FILE,
    TORRC_PATH,
)
from torpro.core.exceptions import ProcessError
from torpro.core.logger import Logger
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.proxy.http_bridge import HttpBridgeService


class ServiceState(Enum):
    """Execution status of the Tor daemon."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


@dataclass
class BootstrapStatus:
    """Represents current Tor bootstrap state."""
    percent: int
    summary: str
    is_done: bool


class TorService:
    """Coordinates lifecycle of the Tor daemon and HTTP bridge."""

    BOOTSTRAP_REGEX = re.compile(r"Bootstrapped\s+(\d+)%(?:\s+\((.*?)\))?:\s+(.*)")

    def __init__(self) -> None:
        self.bridge_manager = BridgeManager()
        self.diagnostics = DiagnosticEngine()

    @staticmethod
    def get_pid() -> Optional[int]:
        """Retrieve active Tor process PID from pid file."""
        if not TOR_PID_FILE.exists():
            return None
        try:
            pid = int(TOR_PID_FILE.read_text(encoding="utf-8").strip())
            return pid
        except ValueError:
            return None

    @classmethod
    def is_running(cls) -> bool:
        """Check if Tor daemon process is active."""
        pid = cls.get_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            if TOR_PID_FILE.exists():
                TOR_PID_FILE.unlink(missing_ok=True)
            return False

    def start(
        self,
        mode: str = "snowflake",
        enable_http_bridge: bool = True,
        on_progress: Optional[Callable[[BootstrapStatus], None]] = None,
        timeout: int = BOOTSTRAP_TIMEOUT_SECONDS,
    ) -> bool:
        """Start Tor service with selected bridge transport and monitor bootstrap."""
        if self.is_running():
            Logger.warning(f"Tor is already running (PID: {self.get_pid()})")
            if enable_http_bridge and not HttpBridgeService.is_running():
                HttpBridgeService.start_background()
            return True

        # 1. Build dynamic configuration FIRST
        Logger.info(f"Configuring bridge mode: {mode.upper()}")
        self.bridge_manager.build_torrc(mode_name=mode)

        # 2. Run pre-flight diagnostic checks
        Logger.info("Running pre-flight diagnostic checks...")
        if not self.diagnostics.is_healthy():
            Logger.warning("Diagnostic check encountered warnings/errors. Running doctor report...")
            self.diagnostics.run_all(print_report=True)

        # Clear old log
        if TOR_LOG_FILE.exists():
            TOR_LOG_FILE.unlink()

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Environment with LD_LIBRARY_PATH
        env = os.environ.copy()
        if LIB_DIR.exists():
            existing_ld = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = f"{LIB_DIR}:{existing_ld}".rstrip(":")

        # Launch Tor process
        Logger.info("Launching Tor process...")
        cmd = [str(TOR_BIN), "-f", str(TORRC_PATH)]

        with open(TOR_LOG_FILE, "a", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=log_handle,
                env=env,
                start_new_session=True,
            )

        TOR_PID_FILE.write_text(str(process.pid), encoding="utf-8")
        Logger.info(f"Tor process started (PID: {process.pid})")

        # Start HTTP bridge
        if enable_http_bridge:
            HttpBridgeService.start_background()

        # Monitor bootstrap progress
        try:
            success = self._wait_for_bootstrap(timeout=timeout, on_progress=on_progress)
            if not success:
                Logger.error(
                    "Tor connection timed out or failed to reach 100% bootstrap.",
                    details=f"Inspect logs with './tor.sh logs' or file: {TOR_LOG_FILE}",
                )
                return False

            Logger.success("Tor connected successfully (100% Bootstrap)!")
            return True
        except KeyboardInterrupt:
            Logger.warning("Connection bootstrap interrupted by user. Stopping services...")
            self.stop()
            return False

    def stop(self) -> bool:
        """Stop Tor daemon and HTTP bridge processes gracefully."""
        HttpBridgeService.stop()

        pid = self.get_pid()
        if not pid:
            Logger.info("Tor is not running.")
            return True

        Logger.info(f"Stopping Tor daemon (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if not self.is_running():
                    break
                time.sleep(0.1)

            if self.is_running():
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as err:
            Logger.error(f"Error stopping Tor PID {pid}", str(err))

        if TOR_PID_FILE.exists():
            TOR_PID_FILE.unlink(missing_ok=True)

        Logger.success("Tor service stopped.")
        return True

    def restart(self, mode: str = "snowflake") -> bool:
        """Restart Tor daemon with chosen mode."""
        Logger.info("Restarting Tor service...")
        self.stop()
        time.sleep(1)
        return self.start(mode=mode)

    def _wait_for_bootstrap(
        self,
        timeout: int = BOOTSTRAP_TIMEOUT_SECONDS,
        on_progress: Optional[Callable[[BootstrapStatus], None]] = None,
    ) -> bool:
        """Tail log file and track bootstrap percentage."""
        start_time = time.time()
        last_percent = -1

        while (time.time() - start_time) < timeout:
            if not self.is_running():
                Logger.error("Tor process exited unexpectedly during bootstrap.")
                return False

            status = self.parse_current_bootstrap()
            if status:
                if status.percent != last_percent:
                    last_percent = status.percent
                    if on_progress:
                        on_progress(status)
                    else:
                        Logger.info(f"Connecting to Tor: {status.percent}% - {status.summary}")

                if status.is_done or status.percent == 100:
                    return True

            time.sleep(0.5)

        return False

    @classmethod
    def parse_current_bootstrap(cls) -> Optional[BootstrapStatus]:
        """Read the log file and return latest bootstrap state."""
        if not TOR_LOG_FILE.exists():
            return None

        try:
            with open(TOR_LOG_FILE, "r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()

            latest_status: Optional[BootstrapStatus] = None
            for line in lines:
                match = cls.BOOTSTRAP_REGEX.search(line)
                if match:
                    percent = int(match.group(1))
                    tag = match.group(2) or ""
                    summary = match.group(3) or tag
                    latest_status = BootstrapStatus(
                        percent=percent,
                        summary=summary,
                        is_done=(percent == 100),
                    )
            return latest_status
        except Exception:
            return None
