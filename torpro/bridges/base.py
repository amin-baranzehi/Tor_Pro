"""Base strategy interface for bridge configurations.

Follows Strategy and Open/Closed principles to allow dynamic swapping and
extension of censorship circumvention transports.
"""

from abc import ABC, abstractmethod
from typing import List


class BaseBridgeStrategy(ABC):
    """Abstract base class for all bridge circumvention strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier for the strategy."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the transport mechanism."""
        pass

    @abstractmethod
    def generate_config_lines(self) -> List[str]:
        """Generate torrc directives specific to this bridge transport."""
        pass
