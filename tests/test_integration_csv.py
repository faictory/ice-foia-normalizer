import csv
import json
import re
from pathlib import Path

import pytest

from ice_foia_normalizer.cli import main
from ice_foia_normalizer.record import CANONICAL_COLUMNS


class TestIntegrationCSVSampleFixture:
    """Integration test: full CSV run on the sample fixture."""

    def test_sample_fixture_end_to_end(self, tmp_path, capsys):
        """Test the complete end-to-end flow on examples/sample.csv."""
        input_file = Path("examples/sample.csv")
        output_file = tmp_path / "sample.normalized.csv"
        rejects_file = tmp_path / "sample.rejects.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([
                str(input_file),
                "-o", str(output_file),
                "--rejects", str(rejects_file),
                "--report", "json",
            ])

        assert exc_info.value.code == 0

        # Capture the report from stdout
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        # Assert the reported counts
        assert report["rows_ingested"] == 12
        assert report["rows_normalized"] == 10
        assert report["rows_rejected"] == 2
        assert report["rows_ingested"] == report["rows_normalized"] + report["rows_rejected"]

        # Read and verify the clean CSV
        with open(output_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            clean_rows = list(reader)

        # Assert the header is exactly the canonical columns in order
        assert headers == CANONICAL_COLUMNS

        # Assert every clean row has an event_date in ISO format YYYY-MM-DD
        iso_date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for row in clean_rows:
            assert iso_date_pattern.match(row['event_date']), \
                f"event_date '{row['event_date']}' does not match ISO format YYYY-MM-DD"

        # Read and verify the rejects CSV
        with open(rejects_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            reject_rows = list(reader)

        # Assert we have exactly 2 rejects
        assert len(reject_rows) == 2

        # Assert each reject has __source_row and __reject_reason populated
        for reject_row in reject_rows:
            assert '__source_row' in reject_row
            assert '__reject_reason' in reject_row
            assert reject_row['__source_row'], "Missing __source_row value"
            assert reject_row['__reject_reason'], "Missing __reject_reason value"
