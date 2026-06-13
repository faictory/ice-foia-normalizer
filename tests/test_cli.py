import json
import sqlite3

import pytest

from ice_foia_normalizer.cli import main


class TestCLIDefaultInvocation:
    """Test default invocation: CSV output, text report, bundled schema."""

    def test_default_run_writes_artifacts_and_exits_0(self, tmp_path):
        """Default CSV run writes both outputs and exits 0."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 0
        output_file = input_file.parent / "input.normalized.csv"
        rejects_file = input_file.parent / "input.rejects.csv"
        assert output_file.exists()
        assert rejects_file.exists()

    def test_default_run_with_coercion_still_exits_0(self, tmp_path):
        """Default run with coercion (no --strict) still exits 0."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender\n"
            "arrest,1/15/2024,NYC,us,Mexico,m\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 0


class TestCLISQLiteFormat:
    """Test --format sqlite output."""

    def test_sqlite_format_writes_to_sqlite_file(self, tmp_path):
        """--format sqlite writes a .sqlite file."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--format", "sqlite"])

        assert exc_info.value.code == 0
        output_file = input_file.parent / "input.normalized.sqlite"
        assert output_file.exists()

        conn = sqlite3.connect(output_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1

    def test_sqlite_with_custom_output_path(self, tmp_path):
        """--format sqlite -o <path> writes to specified path."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )
        output_file = tmp_path / "custom.db"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--format", "sqlite", "-o", str(output_file)])

        assert exc_info.value.code == 0
        assert output_file.exists()


class TestCLIStrictMode:
    """Test --strict flag behavior."""

    def test_strict_with_coercion_exits_3(self, tmp_path):
        """--strict with coercion exits 3, rows still written."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender\n"
            "arrest,1/15/2024,NYC,us,Mexico,m\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--strict"])

        assert exc_info.value.code == 3
        output_file = input_file.parent / "input.normalized.csv"
        assert output_file.exists()

    def test_strict_without_coercion_exits_0(self, tmp_path):
        """--strict with no coercion exits 0."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--strict"])

        assert exc_info.value.code == 0


class TestCLIMissingRequiredColumn:
    """Test exit code 2 for missing required columns."""

    def test_missing_event_type_exits_2_with_column_name(self, tmp_path):
        """Missing event_type exits 2 and names the column in stderr."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_date,field_office,nationality,removal_country,gender\n"
            "2024-01-15,NYC,USA,Mexico,M\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 2

    def test_missing_event_date_exits_2(self, tmp_path):
        """Missing event_date exits 2."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,field_office,nationality,removal_country,gender\n"
            "arrest,NYC,USA,Mexico,M\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 2


class TestCLIErrorHandling:
    """Test error handling and exit codes."""

    def test_missing_input_file_exits_1(self, tmp_path):
        """Missing input file exits 1."""
        input_file = tmp_path / "nonexistent.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 1

    def test_bad_file_extension_exits_1(self, tmp_path):
        """Unsupported file extension exits 1."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("some data")

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 1

    def test_bad_schema_file_exits_1(self, tmp_path):
        """Bad schema file path exits 1."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )
        schema_file = tmp_path / "nonexistent_schema.yaml"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--schema", str(schema_file)])

        assert exc_info.value.code == 1


class TestCLIReportFormats:
    """Test report format output."""

    def test_text_report_default(self, tmp_path, capsys):
        """Default report format is text."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file)])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "ice-foia-normalizer" in captured.out
        assert "rows ingested:" in captured.out.lower()

    def test_json_report_format(self, tmp_path, capsys):
        """--report json outputs JSON format."""
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
        assert report["exit_code"] == 0
        assert "rows_ingested" in report


class TestCLICustomPaths:
    """Test custom output and rejects paths."""

    def test_custom_output_path(self, tmp_path):
        """--output flag writes to custom path."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender,record_id\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M,REC001\n"
        )
        custom_output = tmp_path / "custom_output.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "-o", str(custom_output)])

        assert exc_info.value.code == 0
        assert custom_output.exists()

    def test_custom_rejects_path(self, tmp_path):
        """--rejects flag writes rejects to custom path."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "event_type,event_date,field_office,nationality,removal_country,gender\n"
            "invalid_type,2024-01-15,NYC,USA,Mexico,M\n"
        )
        custom_rejects = tmp_path / "custom_rejects.csv"

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--rejects", str(custom_rejects)])

        assert exc_info.value.code == 0
        assert custom_rejects.exists()


class TestCLIHelp:
    """Test help functionality."""

    def test_help_flag_exits_0(self):
        """--help flag exits 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

    def test_version_flag_exits_0(self):
        """--version flag exits 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0


class TestCLICustomSchema:
    """Test custom schema file."""

    def test_custom_schema_substitutes_mapping(self, tmp_path):
        """--schema flag loads custom mapping."""
        input_file = tmp_path / "input.csv"
        input_file.write_text(
            "type,date,office,nationality,country,gender\n"
            "arrest,2024-01-15,NYC,USA,Mexico,M\n"
        )
        schema_file = tmp_path / "custom_schema.yaml"
        schema_file.write_text(
            """columns:
  event_type:
    - type
  event_date:
    - date
  field_office:
    - office
  nationality: []
  removal_country:
    - country
  gender: []
  record_id: []
required:
  - event_type
  - event_date
"""
        )

        with pytest.raises(SystemExit) as exc_info:
            main([str(input_file), "--schema", str(schema_file)])

        assert exc_info.value.code == 0
        output_file = input_file.parent / "input.normalized.csv"
        assert output_file.exists()
