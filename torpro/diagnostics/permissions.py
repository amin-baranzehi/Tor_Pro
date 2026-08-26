"""Diagnostic check for file and directory permissions."""

import os
from pathlib import Path
from typing import List, Tuple

from torpro.core.constants import (
    BIN_DIR,
    DATA_DIR,
    LOGS_DIR,
    LYREBIRD_BIN,
    SNOWFLAKE_BIN,
    TOR_BIN,
)
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class PermissionTest(BaseDiagnosticTest):
    """Verifies and ensures executable and directory write permissions."""

    def __init__(self, auto_fix: bool = True) -> None:
        self.auto_fix = auto_fix

    @property
    def name(self) -> str:
        return "File & Directory Permissions"

    @property
    def description(self) -> str:
        return "Checks executable permissions on binaries and write access on data/logs."

    def run(self) -> TestResult:
        """Run permissions check and optionally auto-fix."""
        issues: List[str] = []
        fixed: List[str] = []

        # 1. Check directories for write access
        for directory in [DATA_DIR, LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            if not os.access(directory, os.W_OK):
                if self.auto_fix:
                    try:
                        os.chmod(directory, 0o755)
                        fixed.append(f"Granted write access to {directory.name}/")
                    except Exception as err:
                        issues.append(f"Cannot write to directory {directory}: {err}")
                else:
                    issues.append(f"Directory {directory} is not writable.")

        # 2. Check binary executables
        binaries: List[Path] = [TOR_BIN, SNOWFLAKE_BIN, LYREBIRD_BIN]
        for binary in binaries:
            if binary.exists():
                if not os.access(binary, os.X_OK):
                    if self.auto_fix:
                        try:
                            current_mode = os.stat(binary).st_mode
                            os.chmod(binary, current_mode | 0o755)
                            fixed.append(f"Added execute (+x) permission to {binary.name}")
                        except Exception as err:
                            issues.append(f"Cannot set execute bit on {binary.name}: {err}")
                    else:
                        issues.append(f"Binary {binary.name} lacks execute (+x) permission.")

        if issues:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Permission issues detected ({len(issues)} problem(s)).",
                details="\n".join(issues),
                fix_suggestion="Run 'chmod +x bin/* && chmod -R 755 data logs'.",
            )

        if fixed:
            return TestResult(
                name=self.name,
                status=TestStatus.PASS,
                message="Permissions verified and automatically corrected.",
                details="\n".join(fixed),
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message="All binaries and directories have correct permissions.",
        )
