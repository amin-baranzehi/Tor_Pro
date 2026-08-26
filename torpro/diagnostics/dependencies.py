"""Diagnostic check for missing shared libraries and binary runtime dependencies."""

from pathlib import Path
import shutil
from typing import List

from torpro.core.constants import LYREBIRD_BIN, SNOWFLAKE_BIN, TOR_BIN
from torpro.core.process import CommandRunner
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class DependencyTest(BaseDiagnosticTest):
    """Checks for missing dynamic shared libraries (ldd) and test execution."""

    @property
    def name(self) -> str:
        return "Missing Shared Libraries & Dependencies"

    @property
    def description(self) -> str:
        return "Scans binaries with ldd and verifies runtime library resolution."

    def run(self) -> TestResult:
        """Run shared library dependency analysis."""
        has_ldd = shutil.which("ldd") is not None
        missing_libs: List[str] = []
        execution_failures: List[str] = []
        tested_count = 0

        for binary in [TOR_BIN, SNOWFLAKE_BIN, LYREBIRD_BIN]:
            if not binary.exists():
                continue

            tested_count += 1

            # 1. Check with ldd if available
            if has_ldd:
                res = CommandRunner.run(["ldd", str(binary)], timeout=5)
                if res.is_success:
                    for line in res.stdout.splitlines():
                        if "not found" in line:
                            lib_name = line.strip()
                            missing_libs.append(f"{binary.name} -> {lib_name}")

            # 2. Test runtime execution
            if binary == TOR_BIN:
                exec_res = CommandRunner.run([str(binary), "--version"], timeout=5)
                if not exec_res.is_success:
                    execution_failures.append(
                        f"tor execution test failed: {exec_res.stderr or exec_res.stdout}"
                    )
            elif binary in (SNOWFLAKE_BIN, LYREBIRD_BIN):
                exec_res = CommandRunner.run([str(binary), "-version"], timeout=5)
                if exec_res.returncode not in (0, 1, 2):  # Go flags might return 0 or 2 for help
                    execution_failures.append(
                        f"{binary.name} execution test failed (code {exec_res.returncode})"
                    )

        if tested_count == 0:
            return TestResult(
                name=self.name,
                status=TestStatus.WARNING,
                message="No binaries found in bin/ to test dependencies.",
                fix_suggestion="Run './setup.sh' to initialize binaries.",
            )

        if missing_libs:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Missing dynamic libraries detected in {len(missing_libs)} case(s)!",
                details="\n".join(missing_libs),
                fix_suggestion=(
                    "Install missing system libraries (e.g. libevent, libssl, libc) "
                    "or download the standalone bundle via './setup.sh'."
                ),
            )

        if execution_failures:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message="Binary test execution failed despite libraries being present.",
                details="\n".join(execution_failures),
                fix_suggestion="Ensure executable permissions and compatible GLIBC version.",
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message=f"All {tested_count} binaries resolved shared libraries and executed successfully.",
        )
