"""Diagnostic test for file permissions and directory write access."""

import os
from pathlib import Path
from typing import List

from torpro.core.constants import (
    BIN_DIR,
    DATA_DIR,
    LOGS_DIR,
    LYREBIRD_BIN,
    SNOWFLAKE_BIN,
    TOR_BIN,
)
from torpro.core.logger import Logger
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class PermissionTest(BaseDiagnosticTest):
    """Verifies that all binaries are executable (+x) and runtime folders writable."""

    def __init__(self, auto_fix: bool = True) -> None:
        self.auto_fix = auto_fix

    @property
    def name(self) -> str:
        return "File & Directory Permissions"

    @property
    def description(self) -> str:
        return "Checks executable permissions on binaries and write access on data/logs dirs."

    def _fix_ownership_and_mode(self) -> None:
        """Ensure current user owns data and log directories with secure permissions (0700)."""
        current_uid = os.geteuid()
        current_gid = os.getegid()
        for directory in (DATA_DIR, LOGS_DIR):
            directory.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(directory, 0o700)
                if current_uid == 0:
                    os.chown(directory, current_uid, current_gid)
                for root, dirs, files in os.walk(directory):
                    for d in dirs:
                        p = os.path.join(root, d)
                        try:
                            os.chmod(p, 0o700)
                            if current_uid == 0:
                                os.chown(p, current_uid, current_gid)
                        except Exception:
                            pass
                    for f in files:
                        p = os.path.join(root, f)
                        try:
                            os.chmod(p, 0o600)
                            if current_uid == 0:
                                os.chown(p, current_uid, current_gid)
                        except Exception:
                            pass
            except Exception as err:
                Logger.debug(f"Permission adjust warning on {directory}: {err}")

    def run(self) -> TestResult:
        """Execute permission test and auto-heal executable flags if needed."""
        if self.auto_fix:
            self._fix_ownership_and_mode()

        binaries: List[Path] = [TOR_BIN, SNOWFLAKE_BIN, LYREBIRD_BIN]
        missing_exec: List[str] = []

        # Check binaries
        for binary in binaries:
            if not binary.exists():
                return TestResult(
                    name=self.name,
                    status=TestStatus.FAIL,
                    message=f"Binary not found: {binary.name}",
                    fix_suggestion="Run './setup.sh' to download and extract standalone binaries.",
                )
            if not os.access(binary, os.X_OK):
                if self.auto_fix:
                    try:
                        binary.chmod(binary.stat().st_mode | 0o755)
                        Logger.debug(f"Auto-fixed executable permission for {binary.name}")
                    except Exception as err:
                        missing_exec.append(f"{binary.name} ({err})")
                else:
                    missing_exec.append(binary.name)

        if missing_exec:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Missing executable permissions (+x) on: {', '.join(missing_exec)}",
                fix_suggestion=f"Run: chmod +x {BIN_DIR}/*",
            )

        # Check data directory write access
        try:
            test_file = DATA_DIR / ".perm_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except Exception as err:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"DataDirectory '{DATA_DIR}' is not writable: {err}",
                fix_suggestion=f"Run: chown -R $(id -u):$(id -g) '{DATA_DIR}' && chmod 700 '{DATA_DIR}'",
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message="All binaries and directories have correct permissions.",
        )
