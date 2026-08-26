"""Unit tests for the 5-test diagnostic health check engine."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from torpro.core.constants import BIN_DIR, CHECKSUMS_FILE
from torpro.diagnostics.architecture import ArchitectureTest
from torpro.diagnostics.base import TestStatus
from torpro.diagnostics.checksum import ChecksumTest
from torpro.diagnostics.config_syntax import ConfigSyntaxTest
from torpro.diagnostics.dependencies import DependencyTest
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.diagnostics.permissions import PermissionTest


class TestDiagnosticsSuite(unittest.TestCase):
    """Test suite for diagnostic tests."""

    def test_checksum_generator_and_verifier(self):
        """Test checksum generation and dictionary loading."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write("test content for hashing")
            temp_file_path = Path(temp_file.name)

        try:
            expected_hash = hashlib.sha256(b"test content for hashing").hexdigest()
            calc_hash = ChecksumTest.calculate_sha256(temp_file_path)
            self.assertEqual(expected_hash, calc_hash)

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as c_file:
                c_file.write(f"{expected_hash}  {temp_file_path.name}\n")
                c_file_path = Path(c_file.name)

            loaded = ChecksumTest.load_checksums(c_file_path)
            self.assertIn(temp_file_path.name, loaded)
            self.assertEqual(loaded[temp_file_path.name], expected_hash)
            c_file_path.unlink()
        finally:
            temp_file_path.unlink()

    def test_permissions_test_runner(self):
        """Test permissions verification."""
        perm_test = PermissionTest(auto_fix=False)
        self.assertEqual(perm_test.name, "File & Directory Permissions")
        self.assertTrue(hasattr(perm_test, "run"))

    def test_architecture_elf_reader(self):
        """Test architecture detection logic on ELF files."""
        arch_test = ArchitectureTest()
        is_elf, arch_info = arch_test.read_elf_arch("/bin/ls")
        if is_elf:
            self.assertIn("64-bit", arch_info or "32-bit")

    def test_corrupted_config_test(self):
        """Test that invalid config files are flagged properly."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as bad_cfg:
            bad_cfg.write("ThisIsACompletelyInvalidTorConfigOption 12345\n")
            bad_cfg_path = Path(bad_cfg.name)

        try:
            test = ConfigSyntaxTest(config_path=bad_cfg_path)
            res = test.run()
            self.assertIn(res.status, (TestStatus.FAIL, TestStatus.WARNING))
        finally:
            bad_cfg_path.unlink()

    def test_diagnostic_engine(self):
        """Test diagnostic engine registry and execution."""
        engine = DiagnosticEngine()
        results = engine.run_all(print_report=False)
        self.assertEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()
