import json
from collections import OrderedDict

from deportation_foia_normalizer.report import generate_report


def test_text_report_exact_shape():
    """Test that text report reproduces the DESIGN's exact literal shape."""
    report = generate_report(
        input_path="examples/sample.csv",
        output_path="examples/sample.normalized.csv",
        output_format="csv",
        rejects_path="examples/sample.rejects.csv",
        rows_ingested=12,
        rows_normalized=10,
        rows_coerced=7,
        rows_rejected=2,
        column_mappings=OrderedDict([
            ("Event Date", "event_date"),
            ("Apprehension AOR", "field_office"),
            ("Citizenship", "nationality"),
            ("Sex", "gender"),
        ]),
        reject_reasons=OrderedDict([
            ("unparseable event_date", 1),
            ("event_type not in enum", 1),
        ]),
        exit_code=0,
        format="text",
    )

    expected_lines = [
        "deportation-foia-normalizer 1.0.0",
        "input:           examples/sample.csv",
        "output:          examples/sample.normalized.csv (csv)",
        "rejects:         examples/sample.rejects.csv",
        "rows ingested:   12",
        "rows normalized: 10",
        "rows coerced:    7",
        "rows rejected:   2",
        "column mappings:",
        "  Event Date        -> event_date",
        "  Apprehension AOR  -> field_office",
        "  Citizenship       -> nationality",
        "  Sex               -> gender",
        "reject reasons:",
        "  unparseable event_date: 1",
        "  event_type not in enum: 1",
        "exit: 0",
    ]

    expected = "\n".join(expected_lines)
    assert report == expected, f"Text report shape mismatch:\n{repr(report)}\n\nvs\n\n{repr(expected)}"


def test_json_report_structure():
    """Test that JSON report has the correct structure and counts."""
    column_mappings = {
        "Event Date": "event_date",
        "Apprehension AOR": "field_office",
    }
    reject_reasons = {
        "unparseable event_date": 1,
        "event_type not in enum": 1,
    }

    report_json = generate_report(
        input_path="examples/sample.csv",
        output_path="examples/sample.normalized.csv",
        output_format="csv",
        rejects_path="examples/sample.rejects.csv",
        rows_ingested=12,
        rows_normalized=10,
        rows_coerced=7,
        rows_rejected=2,
        column_mappings=column_mappings,
        reject_reasons=reject_reasons,
        exit_code=0,
        format="json",
    )

    data = json.loads(report_json)

    assert "version" in data
    assert "input" in data
    assert "output" in data
    assert "format" in data
    assert "rejects" in data
    assert "rows_ingested" in data
    assert "rows_normalized" in data
    assert "rows_coerced" in data
    assert "rows_rejected" in data
    assert "column_mappings" in data
    assert "reject_reasons" in data
    assert "exit_code" in data

    assert data["input"] == "examples/sample.csv"
    assert data["output"] == "examples/sample.normalized.csv"
    assert data["format"] == "csv"
    assert data["rows_ingested"] == 12
    assert data["rows_normalized"] == 10
    assert data["rows_coerced"] == 7
    assert data["rows_rejected"] == 2
    assert data["exit_code"] == 0
    assert data["column_mappings"] == column_mappings
    assert data["reject_reasons"] == reject_reasons


def test_row_count_invariant():
    """Test that rows_ingested == rows_normalized + rows_rejected."""
    rows_ingested = 12
    rows_normalized = 10
    rows_rejected = 2

    json_report = generate_report(
        input_path="input.csv",
        output_path="output.csv",
        output_format="csv",
        rejects_path="rejects.csv",
        rows_ingested=rows_ingested,
        rows_normalized=rows_normalized,
        rows_coerced=0,
        rows_rejected=rows_rejected,
        column_mappings={},
        reject_reasons={},
        exit_code=0,
        format="json",
    )

    assert rows_ingested == rows_normalized + rows_rejected

    data = json.loads(json_report)
    assert data["rows_ingested"] == data["rows_normalized"] + data["rows_rejected"]
    assert data["rows_coerced"] <= data["rows_normalized"]
