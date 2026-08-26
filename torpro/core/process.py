"""Subprocess execution and command runner utility.

Follows Single Responsibility Principle (SRP) by handling system process
invocations cleanly with proper timeouts and error propagation.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Union

from torpro.core.constants import COMMAND_TIMEOUT_SECONDS
from torpro.core.exceptions import ProcessError
from torpro.core.logger import Logger


@dataclass
class CommandResult:
    """Represents the execution outcome of a shell or system command."""
    command: List[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def is_success(self) -> bool:
        """Return True if command finished with exit code 0."""
        return self.returncode == 0


class CommandRunner:
    """Encapsulates secure, typed execution of operating system commands."""

    @staticmethod
    def run(
        command: List[str],
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = COMMAND_TIMEOUT_SECONDS,
        check: bool = False,
    ) -> CommandResult:
        """Execute a system command and return structured result.

        Args:
            command: Command arguments list.
            cwd: Working directory.
            env: Custom environment variables dict.
            timeout: Timeout in seconds.
            check: If True, raises ProcessError on non-zero exit code.

        Returns:
            CommandResult instance.

        Raises:
            ProcessError: If check is True and command returns non-zero code,
                          or if execution times out.
        """
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        str_cwd = str(cwd) if cwd else None
        cmd_str = " ".join(command)
        Logger.debug(f"Executing: {cmd_str} (cwd={str_cwd})")

        try:
            process = subprocess.run(
                command,
                cwd=str_cwd,
                env=merged_env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            result = CommandResult(
                command=command,
                returncode=process.returncode,
                stdout=process.stdout.strip(),
                stderr=process.stderr.strip(),
            )

            if check and not result.is_success:
                raise ProcessError(
                    f"Command '{cmd_str}' failed with code {result.returncode}",
                    details=result.stderr or result.stdout,
                )
            return result

        except subprocess.TimeoutExpired as err:
            raise ProcessError(
                f"Command '{cmd_str}' timed out after {timeout} seconds",
                details=str(err),
            ) from err
        except FileNotFoundError as err:
            raise ProcessError(
                f"Executable not found: '{command[0]}'",
                details=str(err),
            ) from err
        except Exception as err:
            raise ProcessError(
                f"Failed to execute '{cmd_str}'",
                details=str(err),
            ) from err
