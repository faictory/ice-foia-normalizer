import shutil
from pathlib import Path

import pytest

from ice_foia_normalizer.cli import main


class TestIntegrationPaths:
    """Test output and rejects path handling: defaults vs explicit paths."""

    def test_default_paths_beside_input(self, tmp_path):
        """Default run: clean table and rejects beside input with derived names."""
        input_dir = tmp_path / "input_dir"
        input_dir.mkdir()
        input_file = input_dir / "sample.csv"

        sample_path = Path(__file__).parent.parent / "examples" / "sample.csv"
        shutil.copy(sample_path, input_file)

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 0

        expected_output = input_dir / "sample.normalized.csv"
        expected_rejects = input_dir / "sample.rejects.csv"

        assert expected_output.exists(), f"Expected output file not found at {expected_output}"
        assert expected_rejects.exists(), f"Expected rejects file not found at {expected_rejects}"

        files_in_dir = list(input_dir.iterdir())
        assert len(files_in_dir) == 3, f"Expected 3 files (input, output, rejects) in {input_dir}, got {len(files_in_dir)}: {files_in_dir}"

    def test_explicit_paths_honors_custom_locations(self, tmp_path):
        """Explicit -o/--rejects: artifacts written to specified paths only."""
        input_dir = tmp_path / "input_dir"
        output_dir = tmp_path / "output_dir"
        rejects_dir = tmp_path / "rejects_dir"

        input_dir.mkdir()
        output_dir.mkdir()
        rejects_dir.mkdir()

        input_file = input_dir / "sample.csv"
        sample_path = Path(__file__).parent.parent / "examples" / "sample.csv"
        shutil.copy(sample_path, input_file)

        custom_output = output_dir / "results.csv"
        custom_rejects = rejects_dir / "bad_rows.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "-o", str(custom_output), "--rejects", str(custom_rejects)])

        assert exc_info.value.code == 0

        assert custom_output.exists(), f"Custom output file not found at {custom_output}"
        assert custom_rejects.exists(), f"Custom rejects file not found at {custom_rejects}"

        default_output = input_dir / "sample.normalized.csv"
        default_rejects = input_dir / "sample.rejects.csv"

        assert not default_output.exists(), f"Default output file should NOT exist at {default_output}"
        assert not default_rejects.exists(), f"Default rejects file should NOT exist at {default_rejects}"

        files_in_input_dir = list(input_dir.iterdir())
        assert len(files_in_input_dir) == 1, f"Input dir should only contain input file, got {len(files_in_input_dir)}: {files_in_input_dir}"
