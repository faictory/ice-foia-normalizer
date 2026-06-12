import csv
import sqlite3
import tempfile
from pathlib import Path

import pytest

from deportation_foia_normalizer.writers import (
    write_canonical_csv,
    write_rejects_csv,
    write_sqlite,
)
from deportation_foia_normalizer.record import CANONICAL_COLUMNS


def test_write_canonical_csv_creates_file_with_header():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "output.csv"
        records = [
            {
                "record_id": "1",
                "event_type": "arrest",
                "event_date": "2020-01-01",
                "field_office": "NYC",
                "nationality": "MX",
                "removal_country": "MX",
                "gender": "M",
            },
            {
                "record_id": "2",
                "event_type": "removal",
                "event_date": "2020-02-01",
                "field_office": "LAX",
                "nationality": "SV",
                "removal_country": "SV",
                "gender": "F",
            },
        ]

        write_canonical_csv(path, records)

        assert path.exists()
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert reader.fieldnames == CANONICAL_COLUMNS
            assert len(rows) == 2
            assert rows[0]["record_id"] == "1"
            assert rows[1]["record_id"] == "2"


def test_write_canonical_csv_creates_parent_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "nested" / "output.csv"
        records = [
            {
                "record_id": "1",
                "event_type": "arrest",
                "event_date": "2020-01-01",
                "field_office": "NYC",
                "nationality": "MX",
                "removal_country": "MX",
                "gender": "M",
            }
        ]

        write_canonical_csv(path, records)

        assert path.exists()
        assert path.parent.exists()


def test_write_sqlite_creates_database():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "output.db"
        records = [
            {
                "record_id": "1",
                "event_type": "arrest",
                "event_date": "2020-01-01",
                "field_office": "NYC",
                "nationality": "MX",
                "removal_country": "MX",
                "gender": "M",
            },
            {
                "record_id": "2",
                "event_type": "removal",
                "event_date": "2020-02-01",
                "field_office": "LAX",
                "nationality": "SV",
                "removal_country": "SV",
                "gender": "F",
            },
        ]

        write_sqlite(path, records)

        assert path.exists()
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'")
        assert cursor.fetchone() is not None

        cursor.execute(f"SELECT * FROM records")
        rows = cursor.fetchall()
        assert len(rows) == 2
        conn.close()


def test_write_sqlite_has_correct_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "output.db"
        records = [
            {
                "record_id": "1",
                "event_type": "arrest",
                "event_date": "2020-01-01",
                "field_office": "NYC",
                "nationality": "MX",
                "removal_country": "MX",
                "gender": "M",
            }
        ]

        write_sqlite(path, records)

        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(records)")
        columns = [row[1] for row in cursor.fetchall()]
        assert columns == CANONICAL_COLUMNS
        conn.close()


def test_write_rejects_csv_preserves_original_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "rejects.csv"
        original_headers = ["col1", "col2", "col3"]
        reject_records = [
            {
                "col1": "val1",
                "col2": "val2",
                "col3": "val3",
                "__source_row": 1,
                "__reject_reason": "invalid date",
            },
            {
                "col1": "val4",
                "col2": "val5",
                "col3": "val6",
                "__source_row": 2,
                "__reject_reason": "missing required field",
            },
        ]

        write_rejects_csv(path, original_headers, reject_records)

        assert path.exists()
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            assert fieldnames == ["col1", "col2", "col3", "__source_row", "__reject_reason"]
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["col1"] == "val1"
            assert rows[0]["__source_row"] == "1"
            assert rows[0]["__reject_reason"] == "invalid date"
            assert rows[1]["col1"] == "val4"
            assert rows[1]["__source_row"] == "2"


def test_write_rejects_csv_creates_parent_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "nested" / "rejects.csv"
        original_headers = ["col1"]
        reject_records = [{"col1": "val1", "__source_row": 1, "__reject_reason": "test"}]

        write_rejects_csv(path, original_headers, reject_records)

        assert path.exists()
