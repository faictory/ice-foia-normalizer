import shutil
import subprocess
import sys
from pathlib import Path


class TestE2EStrict:
    """E2E tests for --strict flag using subprocess and module entrypoint."""

    def test_strict_with_coercion_exits_3(self, tmp_path):
        """Run with --strict on coercion-bearing input exits 3."""
        input_file = tmp_path / "sample.csv"
        sample_path = Path(__file__).parent.parent / "examples" / "sample.csv"
        shutil.copy(sample_path, input_file)

        result = subprocess.run(
            [sys.executable, "-m", "ice_foia_normalizer", str(input_file), "--strict"],
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 3

    def test_without_strict_with_coercion_exits_0(self, tmp_path):
        """Run without --strict on coercion-bearing input exits 0."""
        input_file = tmp_path / "sample.csv"
        sample_path = Path(__file__).parent.parent / "examples" / "sample.csv"
        shutil.copy(sample_path, input_file)

        result = subprocess.run(
            [sys.executable, "-m", "ice_foia_normalizer", str(input_file)],
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
