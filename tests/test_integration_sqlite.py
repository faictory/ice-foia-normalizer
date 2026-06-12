import csv
import sqlite3
from pathlib import Path

import pytest

from deportation_foia_normalizer.cli import main
from deportation_foia_normalizer.record import CANONICAL_COLUMNS


class TestIntegrationSQLiteOutput:
    """Integration test: SQLite output table matches CSV normalization."""

    def test_sqlite_output_matches_csv_on_sample_data(self, tmp_path):
        """Assert sqlite --format output matches canonical CSV output on examples/sample.csv."""
        # Path to the bundled sample file
        sample_file = Path(__file__).parent.parent / "examples" / "sample.csv"
        assert sample_file.exists(), f"Sample file not found at {sample_file}"

        # Run CLI with CSV output
        csv_output = tmp_path / "sample.normalized.csv"
        with pytest.raises(SystemExit) as exc_info:
            main([str(sample_file), "-o", str(csv_output)])
        assert exc_info.value.code == 0
        assert csv_output.exists()

        # Run CLI with SQLite output
        sqlite_output = tmp_path / "sample.normalized.sqlite"
        with pytest.raises(SystemExit) as exc_info:
            main([str(sample_file), "--format", "sqlite", "-o", str(sqlite_output)])
        assert exc_info.value.code == 0
        assert sqlite_output.exists()

        # Read CSV records
        csv_records = []
        with open(csv_output, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_records = list(reader)

        # Read SQLite records
        conn = sqlite3.connect(sqlite_output)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Assert records table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"
        )
        assert cursor.fetchone() is not None, "Table 'records' does not exist"

        # Assert columns match canonical columns
        cursor.execute("PRAGMA table_info(records)")
        table_columns = [row[1] for row in cursor.fetchall()]
        assert table_columns == CANONICAL_COLUMNS, (
            f"Columns mismatch: expected {CANONICAL_COLUMNS}, got {table_columns}"
        )

        # Assert row count matches
        cursor.execute("SELECT COUNT(*) FROM records")
        sqlite_row_count = cursor.fetchone()[0]
        assert sqlite_row_count == len(csv_records), (
            f"Row count mismatch: CSV has {len(csv_records)}, SQLite has {sqlite_row_count}"
        )

        # Assert row values match
        cursor.execute(f"SELECT {', '.join(CANONICAL_COLUMNS)} FROM records")
        sqlite_records = cursor.fetchall()
        conn.close()

        for i, (sqlite_row, csv_row) in enumerate(zip(sqlite_records, csv_records)):
            for col in CANONICAL_COLUMNS:
                sqlite_val = sqlite_row[col]
                csv_val = csv_row[col]
                assert sqlite_val == csv_val, (
                    f"Value mismatch at row {i}, column '{col}': "
                    f"SQLite={sqlite_val!r}, CSV={csv_val!r}"
                )
