import argparse
import sys
from pathlib import Path

from ice_foia_normalizer import __version__
from ice_foia_normalizer.readers import read_input
from ice_foia_normalizer.schema_config import (
    load_schema,
    resolve_columns,
    MissingRequiredColumnError,
    SchemaLoadError,
)
from ice_foia_normalizer.normalize import normalize_rows
from ice_foia_normalizer.writers import (
    write_canonical_csv,
    write_sqlite,
    write_rejects_csv,
)
from ice_foia_normalizer.report import generate_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ice-foia-normalizer",
        description="Normalize deportation FOIA records",
    )

    parser.add_argument("input", help="Path to input CSV or XLSX file")
    parser.add_argument(
        "-o",
        "--output",
        help="Destination for clean canonical table (default: <INPUT-stem>.normalized.csv or .sqlite)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "sqlite"],
        default="csv",
        help="Output table format (default: csv)",
    )
    parser.add_argument(
        "--rejects",
        help="Destination for rejects file (default: <INPUT-stem>.rejects.csv)",
    )
    parser.add_argument(
        "--report",
        choices=["text", "json"],
        default="text",
        help="Format of summary report (default: text)",
    )
    parser.add_argument(
        "--schema",
        help="Path to custom canonical-schema/mapping config (YAML or JSON)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat any value coercion as a failure (exit code 3)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ice-foia-normalizer {__version__}",
    )

    args = parser.parse_args(argv)

    exit_code = 0

    try:
        input_path = Path(args.input)

        # Determine output and rejects paths
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_stem(f"{input_path.stem}.normalized")
            if args.format == "sqlite":
                output_path = output_path.with_suffix(".sqlite")
            else:
                output_path = output_path.with_suffix(".csv")

        if args.rejects:
            rejects_path = Path(args.rejects)
        else:
            rejects_path = input_path.with_stem(f"{input_path.stem}.rejects").with_suffix(
                ".csv"
            )

        # Read input
        try:
            headers, rows = read_input(input_path)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            print_exit_code_report(1, args.report)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print_exit_code_report(1, args.report)
            sys.exit(1)

        # Load schema
        try:
            schema = load_schema(args.schema)
        except SchemaLoadError as e:
            print(f"Error: {e}", file=sys.stderr)
            print_exit_code_report(1, args.report)
            sys.exit(1)

        # Resolve columns
        try:
            column_mapping = resolve_columns(headers, schema)
        except MissingRequiredColumnError as e:
            print(
                f"Error: Required column '{e.missing_column}' not found. Available headers: {e.source_headers}",
                file=sys.stderr,
            )
            print_exit_code_report(2, args.report)
            sys.exit(2)

        # Normalize rows
        result = normalize_rows(headers, rows, column_mapping)

        clean_records = result["clean_records"]
        reject_records = result["reject_records"]
        rows_ingested = result["rows_ingested"]
        rows_normalized = result["rows_normalized"]
        rows_rejected = result["rows_rejected"]
        rows_coerced = result["rows_coerced"]
        reject_reasons = result["reject_reasons"]

        # Write output
        if args.format == "sqlite":
            write_sqlite(output_path, clean_records)
        else:
            write_canonical_csv(output_path, clean_records)

        # Write rejects
        write_rejects_csv(rejects_path, headers, reject_records)

        # Check strict mode
        if args.strict and rows_coerced > 0:
            exit_code = 3
        else:
            exit_code = 0

        # Generate and print report
        report = generate_report(
            input_path=str(input_path),
            output_path=str(output_path),
            output_format=args.format,
            rejects_path=str(rejects_path),
            rows_ingested=rows_ingested,
            rows_normalized=rows_normalized,
            rows_coerced=rows_coerced,
            rows_rejected=rows_rejected,
            column_mappings=column_mapping,
            reject_reasons=dict(reject_reasons),
            exit_code=exit_code,
            format=args.report,
        )

        print(report)
        sys.exit(exit_code)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print_exit_code_report(1, args.report)
        sys.exit(1)


def print_exit_code_report(exit_code, report_format):
    """Print minimal report with exit code when errors occur early."""
    if report_format == "json":
        import json
        print(json.dumps({"exit_code": exit_code}))
    else:
        print(f"exit: {exit_code}")
