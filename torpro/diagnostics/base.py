"""Base abstractions and models for the diagnostic test suite.

Follows Open/Closed and Liskov Substitution principles by defining a standard
interface that all diagnostic checks must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TestStatus(Enum):
    """Execution status of a diagnostic test."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    """Standardized outcome of a diagnostic check."""
    name: str
    status: TestStatus
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None

    @property
    def is_passed(self) -> bool:
        """Return True if status is PASS or SKIPPED."""
        return self.status in (TestStatus.PASS, TestStatus.SKIPPED)


class BaseDiagnosticTest(ABC):
    """Abstract base class for all Tor Pro diagnostic checks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the test."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what the test verifies."""
        pass

    @abstractmethod
    def run(self) -> TestResult:
        """Execute the diagnostic test and return a TestResult."""
        pass
