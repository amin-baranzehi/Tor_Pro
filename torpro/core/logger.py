"""Centralized logger, ASCII banner, and output formatter for Tor Pro.

Adheres to PEP 8 and DRY principles by providing standardized console formatting,
colors, and structured log outputs without non-standard emojis.
"""

from datetime import datetime
import sys
from typing import Optional

from torpro import __version__
from torpro.core.constants import AnsiColor


class Logger:
    """Provides formatted, colorized console logging and message outputs."""

    _verbose: bool = False

    @classmethod
    def set_verbose(cls, verbose: bool) -> None:
        """Enable or disable verbose debug output."""
        cls._verbose = verbose

    @staticmethod
    def get_banner() -> str:
        """Return the official Tor Pro ASCII art banner with author info."""
        r = AnsiColor.BRIGHT_RED
        w = AnsiColor.WHITE
        b = AnsiColor.BRIGHT_BLUE
        g = AnsiColor.BRIGHT_GREEN
        y = AnsiColor.BRIGHT_YELLOW
        p = AnsiColor.BRIGHT_MAGENTA
        reset = AnsiColor.RESET
        bold = AnsiColor.BOLD

        art = (
            r + bold + "\n"
            r"  _______ ____  _____    _____  _____   ____  " + "\n"
            r" |__   __/ __ \|  __ \  |  __ \|  __ \ / __ \ " + "\n"
            r"    | | | |  | | |__) | | |__) | |__) | |  | |" + "\n"
            r"    | | | |  | |  _  /  |  ___/|  _  /| |  | |" + "\n"
            r"    | | | |__| | | \ \  | |    | | \ \| |__| |" + "\n"
            r"    |_|  \____/|_|  \_\ |_|    |_|  \_\\____/ " + "\n"
            + w + "========================================================================\n"
            + f"  {b}Tor Pro - Professional Anti-Censorship Tor Suite{reset} {y}[v{__version__}]{reset}\n"
            + f"  {g}Author: {y}amin.baranzehi_{reset} | {p}Advanced Privacy & Security Framework{reset}\n"
            + w + "========================================================================"
            + reset
        )
        return art

    @classmethod
    def print_banner(cls) -> None:
        """Print official ASCII banner."""
        print(cls.get_banner())

    @staticmethod
    def _format(prefix: str, color: str, message: str) -> str:
        """Helper to format a message with colored prefix."""
        return f"{color}{AnsiColor.BOLD}[{prefix}]{AnsiColor.RESET} {message}"

    @classmethod
    def info(cls, message: str) -> None:
        """Print an informational message."""
        print(cls._format("INFO", AnsiColor.BRIGHT_BLUE, message))

    @classmethod
    def success(cls, message: str) -> None:
        """Print a success message."""
        print(cls._format("SUCCESS", AnsiColor.BRIGHT_GREEN, message))

    @classmethod
    def warning(cls, message: str) -> None:
        """Print a warning message."""
        print(cls._format("WARNING", AnsiColor.BRIGHT_YELLOW, message))

    @classmethod
    def error(cls, message: str, details: Optional[str] = None) -> None:
        """Print an error message with optional details."""
        print(cls._format("ERROR", AnsiColor.BRIGHT_RED, message), file=sys.stderr)
        if details:
            print(f"  {AnsiColor.DIM}-> {details}{AnsiColor.RESET}", file=sys.stderr)

    @classmethod
    def step(cls, step_num: int, total_steps: int, title: str) -> None:
        """Print a structured pipeline step header."""
        header = f"[{step_num}/{total_steps}] {title}"
        print(f"\n{AnsiColor.BRIGHT_CYAN}{AnsiColor.BOLD}==> {header}{AnsiColor.RESET}")

    @classmethod
    def header(cls, title: str) -> None:
        """Print a clean section header."""
        sep = "=" * 60
        print(f"\n{AnsiColor.BRIGHT_MAGENTA}{AnsiColor.BOLD}{sep}")
        print(f"  {title}")
        print(f"{sep}{AnsiColor.RESET}\n")

    @classmethod
    def debug(cls, message: str) -> None:
        """Print a debug message if verbose mode is enabled."""
        if cls._verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{AnsiColor.DIM}[DEBUG {timestamp}] {message}{AnsiColor.RESET}")
