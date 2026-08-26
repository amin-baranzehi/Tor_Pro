"""Central diagnostic engine to run and report all health checks."""

from typing import List, Optional

from torpro.core.constants import AnsiColor
from torpro.core.logger import Logger
from torpro.diagnostics.architecture import ArchitectureTest
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus
from torpro.diagnostics.checksum import ChecksumTest
from torpro.diagnostics.config_syntax import ConfigSyntaxTest
from torpro.diagnostics.dependencies import DependencyTest
from torpro.diagnostics.permissions import PermissionTest


class DiagnosticEngine:
    """Manages test registration, execution, and structured reporting."""

    def __init__(self) -> None:
        self._tests: List[BaseDiagnosticTest] = []
        self._register_default_tests()

    def _register_default_tests(self) -> None:
        """Register the 5 core diagnostic health tests."""
        self.register_test(PermissionTest(auto_fix=True))
        self.register_test(ArchitectureTest())
        self.register_test(ChecksumTest())
        self.register_test(DependencyTest())
        self.register_test(ConfigSyntaxTest())

    def register_test(self, test: BaseDiagnosticTest) -> None:
        """Register a new diagnostic test instance."""
        self._tests.append(test)

    def run_all(self, print_report: bool = True) -> List[TestResult]:
        """Execute all registered tests and optionally print report."""
        results: List[TestResult] = []

        if print_report:
            Logger.header("Tor Pro Diagnostic Health Check (Doctor)")

        for index, test in enumerate(self._tests, start=1):
            try:
                res = test.run()
            except Exception as err:
                res = TestResult(
                    name=test.name,
                    status=TestStatus.FAIL,
                    message=f"Unhandled test exception: {err}",
                    details=str(err),
                )
            results.append(res)

            if print_report:
                self._print_test_result(index, res)

        if print_report:
            self._print_summary(results)

        return results

    def is_healthy(self) -> bool:
        """Run all tests and return True if all mandatory checks pass."""
        results = self.run_all(print_report=False)
        return all(r.status != TestStatus.FAIL for r in results)

    @staticmethod
    def _print_test_result(index: int, res: TestResult) -> None:
        """Print a single test outcome with appropriate color and symbol."""
        if res.status == TestStatus.PASS:
            badge = f"{AnsiColor.BRIGHT_GREEN}[PASS]{AnsiColor.RESET}"
        elif res.status == TestStatus.WARNING:
            badge = f"{AnsiColor.BRIGHT_YELLOW}[WARN]{AnsiColor.RESET}"
        elif res.status == TestStatus.SKIPPED:
            badge = f"{AnsiColor.DIM}[SKIP]{AnsiColor.RESET}"
        else:
            badge = f"{AnsiColor.BRIGHT_RED}[FAIL]{AnsiColor.RESET}"

        print(f" {AnsiColor.BOLD}{index}.{AnsiColor.RESET} {badge} {AnsiColor.BOLD}{res.name}{AnsiColor.RESET}")
        print(f"    {AnsiColor.DIM}->{AnsiColor.RESET} {res.message}")

        if res.details:
            for detail_line in res.details.splitlines()[:5]:
                print(f"      {AnsiColor.DIM}{detail_line}{AnsiColor.RESET}")

        if res.fix_suggestion and res.status in (TestStatus.FAIL, TestStatus.WARNING):
            print(f"      {AnsiColor.BRIGHT_CYAN}Fix: {res.fix_suggestion}{AnsiColor.RESET}")
        print()

    @staticmethod
    def _print_summary(results: List[TestResult]) -> None:
        """Print overall diagnostic summary."""
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        warned = sum(1 for r in results if r.status == TestStatus.WARNING)
        failed = sum(1 for r in results if r.status == TestStatus.FAIL)
        total = len(results)

        print(f"{AnsiColor.BOLD}{'=' * 60}{AnsiColor.RESET}")
        if failed == 0:
            print(
                f"{AnsiColor.BRIGHT_GREEN}{AnsiColor.BOLD}"
                f"[OK] System Health Status: HEALTHY ({passed}/{total} passed"
                + (f", {warned} warnings" if warned else "")
                + f"){AnsiColor.RESET}\n"
            )
        else:
            print(
                f"{AnsiColor.BRIGHT_RED}{AnsiColor.BOLD}"
                f"[FAIL] System Health Status: {failed} CRITICAL ISSUE(S) DETECTED!"
                f"{AnsiColor.RESET}\n"
            )
