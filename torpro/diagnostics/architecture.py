"""Diagnostic check for CPU architecture and binary ELF format compatibility."""

import os
import platform
import struct
from typing import Optional, Tuple

from torpro.core.constants import LYREBIRD_BIN, SNOWFLAKE_BIN, TOR_BIN
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class ArchitectureTest(BaseDiagnosticTest):
    """Verifies that ELF binaries match the host machine architecture."""

    # ELF e_machine values
    ELF_MACHINES = {
        0x03: "i386",
        0x3E: "x86_64",
        0x28: "arm",
        0xB7: "aarch64",
    }

    @property
    def name(self) -> str:
        return "CPU Architecture & ELF Compatibility"

    @property
    def description(self) -> str:
        return "Ensures binaries match the host CPU architecture (prevents Exec format error)."

    @classmethod
    def read_elf_arch(cls, binary_path) -> Tuple[bool, Optional[str]]:
        """Read ELF header bytes to identify target architecture."""
        try:
            with open(binary_path, "rb") as handle:
                magic = handle.read(4)
                if magic != b"\x7fELF":
                    return False, "Not an ELF executable"

                # 5th byte: 1=32bit, 2=64bit
                elf_class = handle.read(1)[0]
                # 6th byte: 1=little endian, 2=big endian
                endian = handle.read(1)[0]

                # Seek to e_machine offset (18 for 32-bit and 64-bit)
                handle.seek(18)
                e_machine_bytes = handle.read(2)
                endian_char = "<" if endian == 1 else ">"
                e_machine = struct.unpack(f"{endian_char}H", e_machine_bytes)[0]

                arch_name = cls.ELF_MACHINES.get(e_machine, f"Unknown ({hex(e_machine)})")
                bit_str = "64-bit" if elf_class == 2 else "32-bit"
                return True, f"{arch_name} {bit_str}"
        except Exception as err:
            return False, str(err)

    def run(self) -> TestResult:
        """Run architecture validation test."""
        host_machine = platform.machine().lower()
        if host_machine in ("amd64", "x86_64"):
            expected_arch = "x86_64"
        elif host_machine in ("arm64", "aarch64"):
            expected_arch = "aarch64"
        elif host_machine.startswith("arm"):
            expected_arch = "arm"
        else:
            expected_arch = host_machine

        mismatches = []
        checked = 0

        for binary in [TOR_BIN, SNOWFLAKE_BIN, LYREBIRD_BIN]:
            if not binary.exists():
                continue

            checked += 1
            is_elf, arch_info = self.read_elf_arch(binary)
            if not is_elf:
                mismatches.append(f"{binary.name}: Corrupted or invalid binary ({arch_info})")
                continue

            if expected_arch not in str(arch_info).lower():
                mismatches.append(
                    f"{binary.name}: Binary is built for [{arch_info}], "
                    f"but your system is [{host_machine}]"
                )

        if checked == 0:
            return TestResult(
                name=self.name,
                status=TestStatus.WARNING,
                message="No binaries found in bin/ to check architecture.",
                fix_suggestion="Run './setup.sh' to download matching binaries.",
            )

        if mismatches:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Architecture mismatch detected in {len(mismatches)} binary(ies)!",
                details="\n".join(mismatches),
                fix_suggestion=(
                    f"Download binaries built specifically for your CPU ({host_machine}) "
                    "or run './setup.sh --force'."
                ),
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message=f"All {checked} binaries match host CPU architecture ({host_machine}).",
        )
