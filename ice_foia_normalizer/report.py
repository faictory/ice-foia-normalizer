import json
from ice_foia_normalizer import __version__


def generate_report(
    input_path,
    output_path,
    output_format,
    rejects_path,
    rows_ingested,
    rows_normalized,
    rows_coerced,
    rows_rejected,
    column_mappings,
    reject_reasons,
    exit_code,
    format="text",
):
    """
    Generate either text or JSON summary report of a normalization run.

    Args:
        input_path: Path to input file
        output_path: Path to output file
        output_format: Output format ('csv' or 'sqlite')
        rejects_path: Path to rejects file
        rows_ingested: Number of rows ingested
        rows_normalized: Number of rows normalized successfully
        rows_coerced: Number of rows that required coercion
        rows_rejected: Number of rows rejected
        column_mappings: Dict mapping source column names to canonical names
        reject_reasons: Dict mapping reject reason to count
        exit_code: Exit code for the run
        format: Report format ('text' or 'json')

    Returns:
        String containing the formatted report
    """
    if format == "json":
        return _generate_json_report(
            input_path,
            output_path,
            output_format,
            rejects_path,
            rows_ingested,
            rows_normalized,
            rows_coerced,
            rows_rejected,
            column_mappings,
            reject_reasons,
            exit_code,
        )
    else:
        return _generate_text_report(
            input_path,
            output_path,
            output_format,
            rejects_path,
            rows_ingested,
            rows_normalized,
            rows_coerced,
            rows_rejected,
            column_mappings,
            reject_reasons,
            exit_code,
        )


def _generate_text_report(
    input_path,
    output_path,
    output_format,
    rejects_path,
    rows_ingested,
    rows_normalized,
    rows_coerced,
    rows_rejected,
    column_mappings,
    reject_reasons,
    exit_code,
):
    """Generate text format report."""
    lines = []

    lines.append(f"ice-foia-normalizer {__version__}")

    lines.append(f"input:           {input_path}")
    lines.append(f"output:          {output_path} ({output_format})")
    lines.append(f"rejects:         {rejects_path}")

    lines.append(f"rows ingested:   {rows_ingested}")
    lines.append(f"rows normalized: {rows_normalized}")
    lines.append(f"rows coerced:    {rows_coerced}")
    lines.append(f"rows rejected:   {rows_rejected}")

    lines.append("column mappings:")
    if column_mappings:
        max_source_len = max(len(s) for s in column_mappings.keys())
        for source in column_mappings.keys():
            canonical = column_mappings[source]
            padded_source = source.ljust(max_source_len + 2)
            lines.append(f"  {padded_source}-> {canonical}")

    lines.append("reject reasons:")
    for reason in reject_reasons.keys():
        count = reject_reasons[reason]
        lines.append(f"  {reason}: {count}")

    lines.append(f"exit: {exit_code}")

    return "\n".join(lines)


def _generate_json_report(
    input_path,
    output_path,
    output_format,
    rejects_path,
    rows_ingested,
    rows_normalized,
    rows_coerced,
    rows_rejected,
    column_mappings,
    reject_reasons,
    exit_code,
):
    """Generate JSON format report."""
    report = {
        "version": __version__,
        "input": input_path,
        "output": output_path,
        "format": output_format,
        "rejects": rejects_path,
        "rows_ingested": rows_ingested,
        "rows_normalized": rows_normalized,
        "rows_coerced": rows_coerced,
        "rows_rejected": rows_rejected,
        "column_mappings": column_mappings,
        "reject_reasons": reject_reasons,
        "exit_code": exit_code,
    }

    return json.dumps(report)
