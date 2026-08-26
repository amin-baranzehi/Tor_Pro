"""Unit tests for the 5 diagnostic health checks."""

from pathlib import Path
import tempfile
import unittest

from torpro.diagnostics.architecture import ArchitectureTest
from torpro.diagnostics.base import TestStatus
from torpro.diagnostics.checksum import ChecksumTest
from torpro.diagnostics.config_syntax import ConfigSyntaxTest
from torpro.diagnostics.dependencies import DependencyTest
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.diagnostics.permissions import PermissionTest


class TestDiagnosticsSuite(unittest.TestCase):
    """Test case suite for diagnostic checks."""

    def test_checksum_calculation_and_loading(self):
        """Test SHA256 calculation and checksum loader."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write("hello tor pro")
            temp_file_path = Path(temp_file.name)

        try:
            expected_hash = ChecksumTest.calculate_sha256(temp_file_path)
            self.assertEqual(len(expected_hash), 64)

            # Test checksums file parser
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
        """Test permissions verification and directory creation."""
        perm_test = PermissionTest(auto_fix=True)
        result = perm_test.run()
        self.assertIn(result.status, (TestStatus.PASS, TestStatus.WARNING))

    def test_architecture_elf_reader(self):
        """Test architecture detection logic on ELF files."""
        arch_test = ArchitectureTest()
        # Test on a known system binary
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
            # If tor is not installed, it will warn; if tor is present, it will fail the bad config!
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
