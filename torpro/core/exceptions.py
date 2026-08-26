"""Custom exception hierarchy for Tor Pro.

Follows clean OOP standards by grouping errors into semantic subclasses.
"""


class TorProError(Exception):
    """Base exception for all Tor Pro errors."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class DiagnosticError(TorProError):
    """Raised when a diagnostic health check fails."""
    pass


class ChecksumMismatchError(DiagnosticError):
    """Raised when a binary's SHA256 checksum does not match the expected hash."""
    pass


class PermissionCheckError(DiagnosticError):
    """Raised when executable or directory permissions are insufficient."""
    pass


class ArchitectureMismatchError(DiagnosticError):
    """Raised when binary ELF architecture does not match host machine architecture."""
    pass


class MissingDependencyError(DiagnosticError):
    """Raised when shared libraries (e.g. via ldd) or required tools are missing."""
    pass


class CorruptedConfigError(DiagnosticError):
    """Raised when torrc configuration syntax or bridge definition is invalid."""
    pass


class ConfigError(TorProError):
    """Raised when configuration generation or parsing fails."""
    pass


class ProcessError(TorProError):
    """Raised when starting, stopping, or managing Tor/Proxy processes fails."""
    pass


class ProxyError(TorProError):
    """Raised when the HTTP-to-SOCKS5 proxy server encounters an error."""
    pass


class SystemProxyError(TorProError):
    """Raised when enabling or disabling desktop system proxy settings fails."""
    pass
