import subprocess
import sys
from pathlib import Path


class TestE2EDefaultInvocation:
    """Test process-level default invocation."""

    def test_default_invocation_exits_0_with_text_summary(self):
        """Running `python -m deportation_foia_normalizer examples/sample.csv` exits 0 and outputs text summary."""
        repo_root = Path(__file__).parent.parent
        sample_csv = repo_root / "examples" / "sample.csv"

        result = subprocess.run(
            [sys.executable, "-m", "deportation_foia_normalizer", str(sample_csv)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        # Check exit code
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"

        # Check stdout starts with version line
        assert result.stdout.startswith("deportation-foia-normalizer"), (
            f"stdout should begin with 'deportation-foia-normalizer', got:\n{result.stdout[:100]}"
        )

        # Check for required summary lines (case-insensitive)
        stdout_lower = result.stdout.lower()
        assert "rows ingested:" in stdout_lower, "stdout should contain 'rows ingested:'"
        assert "rows normalized:" in stdout_lower, "stdout should contain 'rows normalized:'"
        assert "rows coerced:" in stdout_lower, "stdout should contain 'rows coerced:'"
        assert "rows rejected:" in stdout_lower, "stdout should contain 'rows rejected:'"
        assert "exit: 0" in result.stdout, "stdout should contain 'exit: 0'"
