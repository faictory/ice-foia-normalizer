import subprocess
import sys


class TestE2EVersionHelp:
    """End-to-end tests for --version and --help using subprocess."""

    def test_version_flag_exits_0_and_prints_version(self):
        """--version flag exits 0 and prints the version line."""
        result = subprocess.run(
            [sys.executable, "-m", "deportation_foia_normalizer", "--version"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "deportation-foia-normalizer 1.0.0" in result.stdout

    def test_help_flag_exits_0_and_prints_usage(self):
        """--help flag exits 0 and prints usage with INPUT arg and flags."""
        result = subprocess.run(
            [sys.executable, "-m", "deportation_foia_normalizer", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Check for INPUT argument
        assert "input" in result.stdout.lower()
        # Check for documented flags
        assert "--output" in result.stdout or "-o" in result.stdout
        assert "--format" in result.stdout
        assert "--rejects" in result.stdout
        assert "--report" in result.stdout
        assert "--schema" in result.stdout
        assert "--strict" in result.stdout
        assert "--version" in result.stdout
        assert "--help" in result.stdout or "-h" in result.stdout
