"""Diagnostic check for verifying binary SHA256 checksums."""

import hashlib
from pathlib import Path
from typing import Dict, Optional

from torpro.core.constants import BIN_DIR, CHECKSUMS_FILE
from torpro.diagnostics.base import BaseDiagnosticTest, TestResult, TestStatus


class ChecksumTest(BaseDiagnosticTest):
    """Verifies the SHA256 checksums of portable binaries against official reference."""

    @property
    def name(self) -> str:
        return "Binary Checksum Verification"

    @property
    def description(self) -> str:
        return "Verifies cryptographic integrity of executables in bin/ using SHA256."

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculate SHA256 digest of a file in streaming chunks."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def load_checksums(checksums_file: Path) -> Dict[str, str]:
        """Load filename-to-hash mapping from checksums file."""
        expected: Dict[str, str] = {}
        if not checksums_file.exists():
            return expected

        with open(checksums_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    hash_val = parts[0].strip()
                    file_name = parts[-1].lstrip("*").strip()
                    expected[file_name] = hash_val
        return expected

    def run(self) -> TestResult:
        """Run the checksum integrity test."""
        if not BIN_DIR.exists():
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message="Binary directory bin/ does not exist.",
                fix_suggestion="Run './setup.sh' to download and initialize binaries.",
            )

        if not CHECKSUMS_FILE.exists():
            return TestResult(
                name=self.name,
                status=TestStatus.WARNING,
                message="Checksums reference file (bin/checksums.sha256) not found.",
                details="Cannot verify binary integrity without checksums file.",
                fix_suggestion="Run './setup.sh' to fetch or regenerate checksums.",
            )

        expected_checksums = self.load_checksums(CHECKSUMS_FILE)
        if not expected_checksums:
            return TestResult(
                name=self.name,
                status=TestStatus.WARNING,
                message="Checksums file is empty.",
                fix_suggestion="Run './setup.sh' to populate checksums.",
            )

        verified_count = 0
        mismatches = []
        missing = []

        for filename, expected_hash in expected_checksums.items():
            target_file = BIN_DIR / filename
            if not target_file.exists():
                missing.append(filename)
                continue

            actual_hash = self.calculate_sha256(target_file)
            if actual_hash.lower() != expected_hash.lower():
                mismatches.append(
                    f"{filename} (expected: {expected_hash[:10]}..., got: {actual_hash[:10]}...)"
                )
            else:
                verified_count += 1

        if mismatches:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Checksum mismatch in {len(mismatches)} binary file(s)!",
                details="\n".join(mismatches),
                fix_suggestion="Run './setup.sh --force' to re-download verified binaries.",
            )

        if missing:
            return TestResult(
                name=self.name,
                status=TestStatus.FAIL,
                message=f"Missing {len(missing)} required binary file(s): {', '.join(missing)}",
                fix_suggestion="Run './setup.sh' to download missing binaries.",
            )

        return TestResult(
            name=self.name,
            status=TestStatus.PASS,
            message=f"All {verified_count} binary checksums match SHA256 references.",
        )
