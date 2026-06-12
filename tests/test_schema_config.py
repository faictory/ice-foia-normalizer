import json
import tempfile
from pathlib import Path

import pytest
import yaml

from deportation_foia_normalizer.schema_config import (
    MissingRequiredColumnError,
    SchemaLoadError,
    load_schema,
    resolve_columns,
)


class TestLoadSchema:
    """Test load_schema function"""

    def test_load_bundled_schema(self):
        """Test loading the bundled default schema"""
        schema = load_schema()
        assert 'alias_map' in schema
        assert 'required' in schema
        assert isinstance(schema['alias_map'], dict)
        assert isinstance(schema['required'], set)

    def test_bundled_schema_has_required_columns(self):
        """Test that bundled schema includes the required columns"""
        schema = load_schema()
        assert 'event_type' in schema['required']
        assert 'event_date' in schema['required']

    def test_load_custom_json_schema(self):
        """Test loading a custom JSON schema file"""
        custom_schema = {
            'columns': {
                'event_date': ['Event Date', 'Apprehension Date'],
                'event_type': ['Event Type'],
            },
            'required': ['event_date', 'event_type'],
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_schema, f)
            temp_path = f.name

        try:
            schema = load_schema(temp_path)
            assert schema['alias_map'] == custom_schema['columns']
            assert 'event_date' in schema['required']
            assert 'event_type' in schema['required']
        finally:
            Path(temp_path).unlink()

    def test_load_custom_yaml_schema(self):
        """Test loading a custom YAML schema file"""
        custom_schema = {
            'columns': {
                'event_date': ['Event Date'],
                'event_type': ['Event Type'],
            },
            'required': ['event_date', 'event_type'],
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_schema, f)
            temp_path = f.name

        try:
            schema = load_schema(temp_path)
            assert schema['alias_map'] == custom_schema['columns']
            assert 'event_date' in schema['required']
        finally:
            Path(temp_path).unlink()

    def test_custom_schema_without_required_still_enforces_required_columns(self):
        """Test that custom schema without 'required' key still enforces REQUIRED_COLUMNS from record"""
        custom_schema = {
            'columns': {
                'event_date': ['Event Date'],
                'event_type': ['Event Type'],
            }
            # Note: no 'required' key
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_schema, f)
            temp_path = f.name

        try:
            schema = load_schema(temp_path)
            # Should still have event_type and event_date as required
            assert 'event_type' in schema['required']
            assert 'event_date' in schema['required']
        finally:
            Path(temp_path).unlink()

    def test_schema_not_found(self):
        """Test that missing schema file raises SchemaLoadError"""
        with pytest.raises(SchemaLoadError) as exc_info:
            load_schema('/nonexistent/path/schema.yaml')
        assert 'not found' in str(exc_info.value).lower()

    def test_malformed_json_schema(self):
        """Test that malformed JSON schema raises SchemaLoadError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json}')
            temp_path = f.name

        try:
            with pytest.raises(SchemaLoadError):
                load_schema(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_malformed_yaml_schema(self):
        """Test that malformed YAML schema raises SchemaLoadError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('{ invalid: yaml: ]')
            temp_path = f.name

        try:
            with pytest.raises(SchemaLoadError):
                load_schema(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_schema_not_dict_raises(self):
        """Test that schema that is not a dict raises SchemaLoadError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(['a', 'list', 'not', 'dict'], f)
            temp_path = f.name

        try:
            with pytest.raises(SchemaLoadError) as exc_info:
                load_schema(temp_path)
            assert 'dict' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_schema_missing_columns_raises(self):
        """Test that schema without 'columns' section raises SchemaLoadError"""
        invalid_schema = {'required': ['event_date']}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_schema, f)
            temp_path = f.name

        try:
            with pytest.raises(SchemaLoadError) as exc_info:
                load_schema(temp_path)
            assert 'columns' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_schema_columns_not_dict_raises(self):
        """Test that 'columns' that is not a dict raises SchemaLoadError"""
        invalid_schema = {'columns': ['a', 'list']}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_schema, f)
            temp_path = f.name

        try:
            with pytest.raises(SchemaLoadError) as exc_info:
                load_schema(temp_path)
            assert 'dict' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_load_schema_with_path_object(self):
        """Test that load_schema works with pathlib.Path objects"""
        custom_schema = {
            'columns': {
                'event_date': ['Event Date'],
                'event_type': ['Event Type'],
            },
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_schema, f)
            temp_path = Path(f.name)

        try:
            schema = load_schema(temp_path)
            assert 'alias_map' in schema
            assert 'required' in schema
        finally:
            temp_path.unlink()


class TestResolveColumns:
    """Test resolve_columns function"""

    def test_resolve_event_date_from_alias(self):
        """Test that 'Event Date' resolves to event_date"""
        schema = load_schema()
        mapping = resolve_columns(['Event Date', 'Event Type'], schema)
        assert mapping['Event Date'] == 'event_date'

    def test_resolve_apprehension_date_to_event_date(self):
        """Test that 'Apprehension Date' resolves to event_date"""
        schema = load_schema()
        mapping = resolve_columns(['Apprehension Date', 'Event Type'], schema)
        assert mapping['Apprehension Date'] == 'event_date'

    def test_both_event_date_and_apprehension_date_resolve(self):
        """Test that both 'Event Date' and 'Apprehension Date' resolve to event_date"""
        schema = load_schema()
        mapping = resolve_columns(
            ['Event Date', 'Apprehension Date', 'Event Type'], schema
        )
        assert mapping['Event Date'] == 'event_date'
        assert mapping['Apprehension Date'] == 'event_date'

    def test_exact_canonical_match_preferred(self):
        """Test that exact canonical name matches are preferred over aliases"""
        schema = load_schema()
        mapping = resolve_columns(['event_date', 'Event Date', 'Event Type'], schema)
        # Both should map to event_date
        assert mapping['event_date'] == 'event_date'
        assert mapping['Event Date'] == 'event_date'

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        schema = load_schema()
        mapping = resolve_columns(['EVENT TYPE', 'event date'], schema)
        assert mapping['EVENT TYPE'] == 'event_type'
        assert mapping['event date'] == 'event_date'

    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed during matching"""
        schema = load_schema()
        mapping = resolve_columns(['  Event Date  ', '  Event Type  '], schema)
        assert mapping['  Event Date  '] == 'event_date'
        assert mapping['  Event Type  '] == 'event_type'

    def test_unmatched_headers_ignored(self):
        """Test that headers that don't match any canonical name or alias are ignored"""
        schema = load_schema()
        mapping = resolve_columns(
            ['Event Date', 'Unknown Column', 'Event Type'], schema
        )
        assert 'Event Date' in mapping
        assert 'Event Type' in mapping
        assert 'Unknown Column' not in mapping

    def test_missing_required_column_raises(self):
        """Test that missing required column raises MissingRequiredColumnError"""
        schema = load_schema()
        with pytest.raises(MissingRequiredColumnError) as exc_info:
            # Only provide Event Date, missing Event Type
            resolve_columns(['Event Date'], schema)

        error = exc_info.value
        assert error.missing_column in ['event_type', 'event_date']
        assert error.source_headers == ['Event Date']

    def test_missing_required_column_error_has_attributes(self):
        """Test that MissingRequiredColumnError has correct attributes"""
        schema = load_schema()
        try:
            resolve_columns(['Apprehension Date'], schema)
            pytest.fail('Expected MissingRequiredColumnError')
        except MissingRequiredColumnError as e:
            assert hasattr(e, 'missing_column')
            assert hasattr(e, 'source_headers')
            assert e.missing_column == 'event_type'
            assert e.source_headers == ['Apprehension Date']

    def test_custom_schema_override(self):
        """Test that custom schema overrides bundled aliases"""
        custom_schema = {
            'columns': {
                'event_date': ['My Date Column'],
                'event_type': ['My Type Column'],
            },
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_schema, f)
            temp_path = f.name

        try:
            schema = load_schema(temp_path)
            mapping = resolve_columns(
                ['My Date Column', 'My Type Column'], schema
            )
            assert mapping['My Date Column'] == 'event_date'
            assert mapping['My Type Column'] == 'event_type'

            # Original aliases should not work
            with pytest.raises(MissingRequiredColumnError):
                resolve_columns(['Event Date', 'Event Type'], schema)
        finally:
            Path(temp_path).unlink()

    def test_empty_source_headers_raises(self):
        """Test that empty source headers raises MissingRequiredColumnError"""
        schema = load_schema()
        with pytest.raises(MissingRequiredColumnError):
            resolve_columns([], schema)

    def test_resolved_mapping_order_preserved(self):
        """Test that resolved mapping preserves the order of source headers"""
        schema = load_schema()
        source_headers = ['Event Type', 'Event Date', 'Record ID']
        mapping = resolve_columns(source_headers, schema)

        # Check that the keys are in the expected order
        keys = list(mapping.keys())
        assert keys[0] == 'Event Type'
        assert keys[1] == 'Event Date'
        assert keys[2] == 'Record ID'

    def test_all_required_columns_present(self):
        """Test that when all required columns are present, no error is raised"""
        schema = load_schema()
        # Provide both required columns
        mapping = resolve_columns(['Event Type', 'Event Date'], schema)
        assert len(mapping) == 2
        assert mapping['Event Type'] == 'event_type'
        assert mapping['Event Date'] == 'event_date'
