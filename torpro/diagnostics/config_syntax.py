"""Diagnostic check for validating Tor configuration syntax and options."""

from pathlib import Path
from typing import Optional

from torpro.core.constants import TOR_BIN, TORRC_PATH
from torpro.core.process import CommandRunner
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class ConfigSyntaxTest(BaseDiagnosticTest):
    """Validates torrc syntax and options using 'tor --verify-config'."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or TORRC_PATH

    @property
    def name(self) -> str:
        return "Corrupted / Invalid Config Verification"

    @property
    def description(self) -> str:
        return "Runs 'tor --verify-config' to catch syntax errors and bad bridge lines."

    def run(self) -> TestResult:
        """Run tor config syntax verification."""
        if not TOR_BIN.exists():
            return TestResult(
                name=self.name,
                status=TestStatus.WARNING,
                message="Cannot verify config: bin/tor is missing.",
                fix_suggestion="Run './setup.sh' first.",
            )

        if not self.config_path.exists():
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Configuration file not found: {self.config_path.name}",
                fix_suggestion="Generate a configuration using './tor.sh start <mode>' or select a bridge in menu.",
            )

        # Check for empty file
        content = self.config_path.read_text(encoding="utf-8").strip()
        if not content:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Configuration file {self.config_path.name} is empty.",
                fix_suggestion="Regenerate configuration from menu or select a bridge mode.",
            )

        # Run verification command
        res = CommandRunner.run(
            [str(TOR_BIN), "--verify-config", "-f", str(self.config_path)],
            timeout=10,
        )

        if not res.is_success:
            error_output = res.stderr or res.stdout
            cleaned_errors = []
            for line in error_output.splitlines():
                if any(k in line for k in ["[warn]", "[err]", "Configuration was", "Failed"]):
                    cleaned_errors.append(line.strip())

            details_msg = "\n".join(cleaned_errors) if cleaned_errors else error_output
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Corrupted or invalid configuration in {self.config_path.name}!",
                details=details_msg,
                fix_suggestion=(
                    "Check bridge definitions, port numbers, or reset config by running "
                    "'./tor.sh start snowflake'."
                ),
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message=f"Configuration file ({self.config_path.name}) syntax is valid and verified by Tor.",
        )
