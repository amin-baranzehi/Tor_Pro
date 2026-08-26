"""Diagnostics test suite package."""

from torpro.diagnostics.architecture import ArchitectureTest
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus
from torpro.diagnostics.checksum import ChecksumTest
from torpro.diagnostics.config_syntax import ConfigSyntaxTest
from torpro.diagnostics.dependencies import DependencyTest
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.diagnostics.permissions import PermissionTest

__all__ = [
    "BaseDiagnosticTest",
    "TestResult",
    "TestStatus",
    "ChecksumTest",
    "PermissionTest",
    "ArchitectureTest",
    "DependencyTest",
    "ConfigSyntaxTest",
    "DiagnosticEngine",
]
