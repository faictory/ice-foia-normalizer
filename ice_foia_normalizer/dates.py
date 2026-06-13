from datetime import datetime
from typing import Optional, Dict, Any

MONTH_ABBR = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

MONTH_FULL = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


def normalize_date(raw: str) -> Optional[Dict[str, Any]]:
    """
    Convert mixed source date formats to ISO-8601.

    Args:
        raw: A date string in one of several supported formats

    Returns:
        A dict with 'date' (ISO string) and 'coerced' (bool) keys if parseable,
        or None if not parseable.

    Supported input formats:
    - YYYY-MM-DD (passed through unchanged, coerced=False)
    - MM/DD/YYYY
    - M/D/YY (two-digit year)
    - Mon D, YYYY (e.g. 'Jan 5, 2026' or 'January 5, 2026')

    Returns None for:
    - Empty or blank strings
    - Impossible dates (e.g. '32/13/2026')
    """
    if not raw or not raw.strip():
        return None

    raw = raw.strip()

    if _is_iso_format(raw):
        try:
            datetime.strptime(raw, '%Y-%m-%d')
            return {'date': raw, 'coerced': False}
        except ValueError:
            return None

    result = _try_format(raw, '%m/%d/%Y')
    if result:
        return {'date': result, 'coerced': True}

    result = _try_format(raw, '%m/%d/%y')
    if result:
        return {'date': result, 'coerced': True}

    result = _try_month_day_year(raw)
    if result:
        return {'date': result, 'coerced': True}

    return None


def _is_iso_format(s: str) -> bool:
    if len(s) != 10:
        return False
    if s[4] != '-' or s[7] != '-':
        return False
    return s[:4].isdigit() and s[5:7].isdigit() and s[8:10].isdigit()


def _try_format(raw: str, fmt: str) -> Optional[str]:
    try:
        dt = datetime.strptime(raw, fmt)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None


def _try_month_day_year(raw: str) -> Optional[str]:
    result = _try_format(raw, '%b %d, %Y')
    if result:
        return result

    result = _try_format(raw, '%B %d, %Y')
    if result:
        return result

    parts = raw.split()
    if len(parts) != 3:
        return None

    month_str = parts[0].lower()
    day_str = parts[1].rstrip(',')
    year_str = parts[2]

    month = MONTH_ABBR.get(month_str[:3]) or MONTH_FULL.get(month_str)
    if not month:
        return None

    try:
        day = int(day_str)
    except ValueError:
        return None

    try:
        year = int(year_str)
    except ValueError:
        return None

    try:
        dt = datetime(year, month, day)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None
