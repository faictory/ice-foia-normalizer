import json
import re
from pathlib import Path

import pytest

from ice_foia_normalizer.cli import main


class TestJSONReportIntegration:
    """Integration test: JSON report object structure and count consistency."""

    def test_json_report_has_all_required_keys(self, tmp_path, capsys):
        """--report json outputs an object with all documented keys."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--report", "json"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        required_keys = {
            "version",
            "input",
            "output",
            "format",
            "rejects",
            "rows_ingested",
            "rows_normalized",
            "rows_coerced",
            "rows_rejected",
            "column_mappings",
            "reject_reasons",
            "exit_code",
        }
        assert required_keys.issubset(report.keys()), f"Missing keys: {required_keys - set(report.keys())}"

    def test_json_report_row_count_invariant(self, tmp_path, capsys):
        """JSON report satisfies rows_ingested == rows_normalized + rows_rejected."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
            "arrest,2024-01-16,NYC,USA,Mexico,F,REC002\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--report", "json"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        assert report["rows_ingested"] == report["rows_normalized"] + report["rows_rejected"]

    def test_json_report_counts_match_text_report(self, tmp_path, capsys):
        """JSON report counts match counts from text-report run."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
            "arrest,2024-01-16,NYC,USA,Mexico,F,REC002\n"
            "invalid_type,2024-01-17,NYC,USA,Mexico,M,REC003\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--report", "text"])

        text_exit_code = exc_info.value.code
        captured_text = capsys.readouterr()
        text_report = captured_text.out

        def extract_count(output, field_name):
            """Extract a count from the text report output."""
            pattern = rf"{field_name}:\s+(\d+)"
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return None

        text_rows_ingested = extract_count(text_report, "rows ingested")
        text_rows_normalized = extract_count(text_report, "rows normalized")
        text_rows_coerced = extract_count(text_report, "rows coerced")
        text_rows_rejected = extract_count(text_report, "rows rejected")

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--report", "json"])

        json_exit_code = exc_info.value.code
        captured_json = capsys.readouterr()
        json_report = json.loads(captured_json.out)

        assert text_exit_code == json_exit_code
        assert json_report["rows_ingested"] == json_report["rows_normalized"] + json_report["rows_rejected"]

        if text_rows_ingested is not None:
            assert json_report["rows_ingested"] == text_rows_ingested
        if text_rows_normalized is not None:
            assert json_report["rows_normalized"] == text_rows_normalized
        if text_rows_coerced is not None:
            assert json_report["rows_coerced"] == text_rows_coerced
        if text_rows_rejected is not None:
            assert json_report["rows_rejected"] == text_rows_rejected

    def test_json_report_with_sample_csv(self, tmp_path, capsys):
        """JSON report works with examples/sample.csv; artifacts in tmp_path."""
        sample_file = Path(__file__).parent.parent / "examples" / "sample.csv"
        assert sample_file.exists(), f"Sample file not found at {sample_file}"

        output_file = tmp_path / "sample.normalized.csv"
        rejects_file = tmp_path / "sample.rejects.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([
                str(sample_file),
                "-o", str(output_file),
                "--rejects", str(rejects_file),
                "--report", "json",
            ])

        assert exc_info.value.code in (0, 3)
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        required_keys = {
            "version",
            "input",
            "output",
            "format",
            "rejects",
            "rows_ingested",
            "rows_normalized",
            "rows_coerced",
            "rows_rejected",
            "column_mappings",
            "reject_reasons",
            "exit_code",
        }
        assert required_keys.issubset(report.keys())
        assert report["rows_ingested"] == report["rows_normalized"] + report["rows_rejected"]
        assert report["exit_code"] in (0, 3)
        assert report["format"] == "csv"
        assert "sample.csv" in report["input"]
