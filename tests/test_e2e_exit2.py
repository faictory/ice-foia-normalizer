import subprocess
import sys


class TestE2EMissingRequiredColumn:
    """E2E test: missing required column exits with code 2 and error details."""

    def test_missing_event_date_exits_2_with_error_details(self, tmp_path):
        """Missing event_date exits 2 with missing column name and source headers in stderr."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,field_office,nationality,removal_country,gender\n"
            "arrest,NYC,USA,Mexico,M\n"
        )

        result = subprocess.run(
            [sys.executable, "-m", "ice_foia_normalizer", str(input_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "event_date" in result.stderr
        assert "event_type" in result.stderr
        assert "field_office" in result.stderr
        assert "Available headers" in result.stderr

    def test_missing_event_type_exits_2_with_error_details(self, tmp_path):
        """Missing event_type exits 2 with missing column name and source headers in stderr."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_date,field_office,nationality,removal_country,gender\n"
            "2024-01-15,NYC,USA,Mexico,M\n"
        )

        result = subprocess.run(
            [sys.executable, "-m", "ice_foia_normalizer", str(input_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "event_type" in result.stderr
        assert "event_date" in result.stderr
        assert "field_office" in result.stderr
        assert "Available headers" in result.stderr
