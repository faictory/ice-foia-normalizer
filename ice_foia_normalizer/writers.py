import csv
import sqlite3
from pathlib import Path

from ice_foia_normalizer.record import CANONICAL_COLUMNS


def write_canonical_csv(path, clean_records):
    """Write clean records to CSV with canonical columns and UTF-8 encoding."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(clean_records)


def write_sqlite(path, clean_records):
    """Write clean records to SQLite database with a 'records' table."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()

    # Create table with all canonical columns as TEXT
    columns_def = ', '.join([f'"{col}" TEXT' for col in CANONICAL_COLUMNS])
    cursor.execute(f'CREATE TABLE records ({columns_def})')

    # Insert records in order
    placeholders = ', '.join(['?' for _ in CANONICAL_COLUMNS])
    col_names = ', '.join([f'"{col}"' for col in CANONICAL_COLUMNS])
    insert_sql = f'INSERT INTO records ({col_names}) VALUES ({placeholders})'

    for record in clean_records:
        values = tuple(record.get(col) for col in CANONICAL_COLUMNS)
        cursor.execute(insert_sql, values)

    conn.commit()
    conn.close()


def write_rejects_csv(path, original_headers, reject_records):
    """Write reject records to CSV with original columns plus __source_row and __reject_reason."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve original headers and add the two annotation columns
    fieldnames = list(original_headers) + ['__source_row', '__reject_reason']

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(reject_records)
