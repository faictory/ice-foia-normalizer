import json
from pathlib import Path

import yaml


class MissingRequiredColumnError(Exception):
    """Raised when required canonical columns cannot be resolved from source headers."""

    def __init__(self, missing_column, source_headers):
        self.missing_column = missing_column
        self.source_headers = source_headers
        super().__init__(
            f"Required column '{missing_column}' not found. Available headers: {source_headers}"
        )


class SchemaLoadError(Exception):
    """Raised when a schema file cannot be loaded or is malformed."""
    pass


def load_schema(path=None):
    """
    Load alias/required config from bundled or custom schema.

    Args:
        path: Optional path to custom schema file (YAML or JSON).
              If None, loads the bundled default_schema.yaml.

    Returns:
        dict with 'alias_map' (canonical -> list of aliases) and 'required' (set of required columns)
    """
    if path is None:
        # Load bundled schema
        schema_path = Path(__file__).parent / "default_schema.yaml"
    else:
        schema_path = Path(path)

    try:
        with open(schema_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        raise SchemaLoadError(f"Schema file not found: {schema_path}")
    except Exception as e:
        raise SchemaLoadError(f"Failed to read schema file: {e}")

    # Detect format and parse
    try:
        if path and (path.endswith('.json') or path.endswith('.JSON')):
            schema_data = json.loads(content)
        else:
            # Try YAML (default or fallback)
            schema_data = yaml.safe_load(content)
    except Exception as e:
        raise SchemaLoadError(f"Failed to parse schema file: {e}")

    if not isinstance(schema_data, dict):
        raise SchemaLoadError("Schema must be a dict")

    # Extract columns (alias map) and required list
    if 'columns' not in schema_data:
        raise SchemaLoadError("Schema missing 'columns' section")

    columns = schema_data['columns']
    required_list = schema_data.get('required', [])

    if not isinstance(columns, dict):
        raise SchemaLoadError("Schema 'columns' section must be a dict")

    return {
        'alias_map': columns,
        'required': set(required_list) if isinstance(required_list, list) else required_list,
    }


def resolve_columns(source_headers, schema):
    """
    Resolve source headers to canonical columns using the schema.

    Args:
        source_headers: List of source header strings
        schema: Dict with 'alias_map' and 'required' keys (from load_schema)

    Returns:
        Ordered dict mapping {source_header: canonical_column}

    Raises:
        MissingRequiredColumnError: If a required canonical column cannot be resolved
    """
    alias_map = schema['alias_map']
    required = schema['required']

    resolved = {}
    resolved_canonicals = set()

    for source_header in source_headers:
        source_normalized = source_header.strip().lower()

        # First check if this exactly matches a canonical name
        canonical_found = None
        for canonical in alias_map.keys():
            if canonical.strip().lower() == source_normalized:
                canonical_found = canonical
                break

        # If not, check aliases
        if not canonical_found:
            for canonical, aliases in alias_map.items():
                if aliases:
                    for alias in aliases:
                        if alias.strip().lower() == source_normalized:
                            canonical_found = canonical
                            break
                if canonical_found:
                    break

        if canonical_found:
            resolved[source_header] = canonical_found
            resolved_canonicals.add(canonical_found)

    # Check if all required columns are present
    missing = required - resolved_canonicals
    if missing:
        missing_col = next(iter(missing))
        raise MissingRequiredColumnError(missing_col, source_headers)

    return resolved
