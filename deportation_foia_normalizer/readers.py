import csv
from pathlib import Path

import openpyxl


def read_input(path):
    """Read a raw FOIA dump into headers and row dicts.

    Args:
        path: Path to a .csv or .xlsx file

    Returns:
        tuple: (headers list, rows list of dicts)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If extension is unsupported
        Exception: If parsing fails
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext == ".csv":
        return _read_csv(path)
    elif ext == ".xlsx":
        return _read_xlsx(path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def _read_csv(path):
    """Read CSV file and return (headers, rows)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty")
            headers = list(reader.fieldnames)
            rows = []
            for row in reader:
                # Normalize None values to empty strings
                normalized_row = {k: (v if v is not None else "") for k, v in row.items()}
                rows.append(normalized_row)
            return (headers, rows)
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Failed to parse CSV: {e}") from e


def _read_xlsx(path):
    """Read XLSX file and return (headers, rows)."""
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active

        rows_iter = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            raise ValueError("XLSX file is empty")

        if header_row is None:
            raise ValueError("XLSX file has no header row")

        headers = [str(h) if h is not None else "" for h in header_row]
        rows = []

        for row_data in rows_iter:
            if row_data is None or all(v is None for v in row_data):
                continue
            row_dict = {}
            for i, header in enumerate(headers):
                value = row_data[i] if i < len(row_data) else None
                row_dict[header] = str(value) if value is not None else ""
            rows.append(row_dict)

        return (headers, rows)
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Failed to parse XLSX: {e}") from e
