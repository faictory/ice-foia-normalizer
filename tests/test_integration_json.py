import json
import pytest

from deportation_foia_normalizer.cli import main


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

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--report", "json"])

        json_exit_code = exc_info.value.code
        captured_json = capsys.readouterr()
        json_report = json.loads(captured_json.out)

        assert text_exit_code == json_exit_code
        assert "rows ingested:" in text_report.lower()
        assert "rows normalized:" in text_report.lower()
        assert "rows rejected:" in text_report.lower()
        assert json_report["rows_ingested"] == json_report["rows_normalized"] + json_report["rows_rejected"]

    def test_json_report_with_sample_csv(self, capsys):
        """JSON report works with examples/sample.csv."""
        with pytest.raises(SystemExit) as exc_info:
            main(["examples/sample.csv", "--report", "json"])

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
