CANONICAL_COLUMNS = [
    "record_id",
    "event_type",
    "event_date",
    "field_office",
    "nationality",
    "removal_country",
    "gender",
]

REQUIRED_COLUMNS = {"event_type", "event_date"}

EVENT_TYPE_VALUES = {"arrest", "detainer", "removal"}

GENDER_VALUES = {"M", "F", "U"}
