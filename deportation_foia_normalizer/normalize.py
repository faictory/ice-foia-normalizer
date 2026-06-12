from collections import Counter

from deportation_foia_normalizer.record import (
    CANONICAL_COLUMNS,
    EVENT_TYPE_VALUES,
    GENDER_VALUES,
)
from deportation_foia_normalizer.dates import normalize_date
from deportation_foia_normalizer.codes import normalize_gender, normalize_event_type


def normalize_rows(source_headers, rows, column_mapping):
    """
    Convert mapped source rows into canonical clean records plus rejects.

    Args:
        source_headers: List of source header strings
        rows: List of row dicts keyed by source_headers
        column_mapping: Dict mapping {source_header: canonical_column}

    Returns:
        A result dict with:
        - clean_records: List of dicts keyed by canonical columns
        - reject_records: List of dicts with original row, __source_row, __reject_reason
        - rows_ingested: Total rows processed
        - rows_normalized: Rows that passed validation
        - rows_rejected: Rows that failed validation
        - rows_coerced: Rows that required field reformatting/mapping
        - reject_reasons: Counter of rejection categories
        - column_mappings: The column_mapping dict used
    """
    clean_records = []
    reject_records = []
    reject_reasons_counter = Counter()
    rows_coerced = 0

    for source_row_index, row in enumerate(rows, start=1):
        record, was_coerced, reject_reason, reject_category = _normalize_row(
            row, source_row_index, column_mapping
        )

        if reject_reason:
            reject_records.append({
                **row,
                '__source_row': source_row_index,
                '__reject_reason': reject_reason,
            })
            reject_reasons_counter[reject_category] += 1
        else:
            clean_records.append(record)
            if was_coerced:
                rows_coerced += 1

    rows_ingested = len(rows)
    rows_normalized = len(clean_records)
    rows_rejected = len(reject_records)

    return {
        'clean_records': clean_records,
        'reject_records': reject_records,
        'rows_ingested': rows_ingested,
        'rows_normalized': rows_normalized,
        'rows_rejected': rows_rejected,
        'rows_coerced': rows_coerced,
        'reject_reasons': reject_reasons_counter,
        'column_mappings': column_mapping,
    }


def _normalize_row(row, source_row_index, column_mapping):
    """
    Normalize a single row.

    Returns a tuple: (record_dict, was_coerced, reject_reason, reject_category)
    - record_dict: Normalized canonical record (or None if rejected)
    - was_coerced: Boolean indicating if any field was coerced
    - reject_reason: String reason for rejection (or None if accepted)
    - reject_category: Category key for the rejection (or None if accepted)
    """
    record = {}
    was_coerced = False

    # Reverse column mapping: canonical -> source header
    canonical_to_source = {v: k for k, v in column_mapping.items()}

    for canonical_col in CANONICAL_COLUMNS:
        source_header = canonical_to_source.get(canonical_col)
        raw_value = row.get(source_header, '') if source_header else ''

        if canonical_col == 'event_date':
            result = normalize_date(raw_value)
            if result is None:
                reason = f'unparseable event_date: "{raw_value}"'
                return None, False, reason, 'unparseable event_date'
            record['event_date'] = result['date']
            if result['coerced']:
                was_coerced = True

        elif canonical_col == 'event_type':
            try:
                normalized, coerced = normalize_event_type(raw_value)
                record['event_type'] = normalized
                if coerced:
                    was_coerced = True
            except ValueError:
                reason = f'event_type not in {EVENT_TYPE_VALUES}: "{raw_value}"'
                return None, False, reason, 'event_type not in enum'

        elif canonical_col == 'gender':
            try:
                normalized, coerced = normalize_gender(raw_value)
                record['gender'] = normalized
                if coerced:
                    was_coerced = True
            except ValueError:
                reason = f'gender value not in {GENDER_VALUES}: "{raw_value}"'
                return None, False, reason, 'gender not in enum'

        elif canonical_col == 'field_office':
            trimmed = str(raw_value).strip() if raw_value else ''
            record['field_office'] = trimmed
            if trimmed != str(raw_value):
                was_coerced = True

        elif canonical_col == 'removal_country':
            trimmed = str(raw_value).strip() if raw_value else ''
            record['removal_country'] = trimmed
            if trimmed != str(raw_value):
                was_coerced = True

        elif canonical_col == 'nationality':
            trimmed_upper = str(raw_value).strip().upper() if raw_value else ''
            record['nationality'] = trimmed_upper
            if trimmed_upper != str(raw_value):
                was_coerced = True

        elif canonical_col == 'record_id':
            raw_record_id = str(raw_value).strip() if raw_value else ''
            if not raw_record_id:
                record['record_id'] = str(source_row_index)
                was_coerced = True
            else:
                record['record_id'] = raw_record_id

    return record, was_coerced, None, None
