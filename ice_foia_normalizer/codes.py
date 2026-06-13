from ice_foia_normalizer.record import EVENT_TYPE_VALUES, GENDER_VALUES


def normalize_gender(raw):
    """Normalize gender codes to canonical enum values.

    Args:
        raw: A gender value from a raw FOIA dump.

    Returns:
        A tuple (normalized_value, was_coerced).

    Raises:
        ValueError: If the raw value is an unrecognized non-blank string.
    """
    if raw is None:
        return 'U', True

    trimmed = str(raw).strip()

    if not trimmed:
        return 'U', True

    upper = trimmed.upper()

    # Map gender codes/values to canonical enum
    gender_map = {
        '1': 'M',
        '2': 'F',
        'M': 'M',
        'F': 'F',
        'MALE': 'M',
        'FEMALE': 'F',
    }

    if upper in gender_map:
        canonical = gender_map[upper]
        was_coerced = trimmed != canonical
        return canonical, was_coerced

    raise ValueError(f'gender value not in {GENDER_VALUES}: "{raw}"')


def normalize_event_type(raw):
    """Normalize event type codes to canonical enum values.

    Args:
        raw: An event type value from a raw FOIA dump.

    Returns:
        A tuple (normalized_value, was_coerced).

    Raises:
        ValueError: If the raw value is not in the canonical enum.
    """
    if raw is None:
        raise ValueError('event_type is required')

    trimmed = str(raw).strip()

    if not trimmed:
        raise ValueError('event_type is required')

    upper = trimmed.upper()

    # Map event type codes/values to canonical enum
    event_type_map = {
        'ARR': 'arrest',
        'ARREST': 'arrest',
        'DET': 'detainer',
        'DETAINER': 'detainer',
        'REM': 'removal',
        'REMOVAL': 'removal',
    }

    if upper in event_type_map:
        canonical = event_type_map[upper]
        was_coerced = trimmed != canonical
        return canonical, was_coerced

    raise ValueError(f'event_type not in {EVENT_TYPE_VALUES}: "{raw}"')
