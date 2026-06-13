from ice_foia_normalizer.normalize import normalize_rows


class TestValidRowsProduceCleanRecords:
    """Rows with valid event_date and event_type should be normalized to clean_records."""

    def test_simple_valid_row(self):
        """A row with all valid fields produces a clean record."""
        source_headers = ['date_col', 'type_col', 'gender_col', 'office_col', 'country_col', 'nationality_col', 'id_col']
        rows = [{
            'date_col': '01/15/2026',
            'type_col': 'arrest',
            'gender_col': 'M',
            'office_col': 'Boston',
            'country_col': 'Mexico',
            'nationality_col': 'mx',
            'id_col': 'rec123',
        }]
        column_mapping = {
            'date_col': 'event_date',
            'type_col': 'event_type',
            'gender_col': 'gender',
            'office_col': 'field_office',
            'country_col': 'removal_country',
            'nationality_col': 'nationality',
            'id_col': 'record_id',
        }

        result = normalize_rows(source_headers, rows, column_mapping)

        assert result['rows_ingested'] == 1
        assert result['rows_normalized'] == 1
        assert result['rows_rejected'] == 0
        assert len(result['clean_records']) == 1
        clean_record = result['clean_records'][0]
        assert clean_record['event_date'] == '2026-01-15'
        assert clean_record['event_type'] == 'arrest'
        assert clean_record['gender'] == 'M'
        assert clean_record['field_office'] == 'Boston'
        assert clean_record['removal_country'] == 'Mexico'
        assert clean_record['nationality'] == 'MX'
        assert clean_record['record_id'] == 'rec123'

    def test_event_type_code_normalization(self):
        """Event type codes (ARR, DET, REM) normalize to canonical values."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'ARR',
            'gender': 'F',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {
            'event_date': 'event_date',
            'event_type': 'event_type',
            'gender': 'gender',
            'field_office': 'field_office',
            'removal_country': 'removal_country',
            'nationality': 'nationality',
            'record_id': 'record_id',
        }

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        assert result['clean_records'][0]['event_type'] == 'arrest'

    def test_iso_date_passthrough(self):
        """ISO-formatted dates pass through without coercion."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'detainer',
            'gender': 'U',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': 'x123',
        }]
        column_mapping = {
            'event_date': 'event_date',
            'event_type': 'event_type',
            'gender': 'gender',
            'field_office': 'field_office',
            'removal_country': 'removal_country',
            'nationality': 'nationality',
            'record_id': 'record_id',
        }

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        assert result['clean_records'][0]['event_date'] == '2026-01-15'


class TestUnparseableEventDateRejection:
    """Rows with unparseable event_date should be rejected."""

    def test_invalid_date_rejected(self):
        """Impossible date (32/13/2026) produces rejection."""
        rows = [{
            'event_date': '32/13/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_ingested'] == 1
        assert result['rows_rejected'] == 1
        assert result['rows_normalized'] == 0
        assert len(result['reject_records']) == 1
        reject = result['reject_records'][0]
        assert reject['__source_row'] == 1
        assert 'unparseable event_date' in reject['__reject_reason']
        assert '32/13/2026' in reject['__reject_reason']
        assert result['reject_reasons']['unparseable event_date'] == 1

    def test_blank_event_date_rejected(self):
        """Blank event_date is unparseable and rejected."""
        rows = [{
            'event_date': '',
            'event_type': 'arrest',
            'gender': '',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_rejected'] == 1
        assert result['reject_reasons']['unparseable event_date'] == 1

    def test_source_row_index_in_reject_record(self):
        """Rejected rows carry their 1-based source row index."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': 'invalid', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/16/2026', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_rejected'] == 1
        assert result['reject_records'][0]['__source_row'] == 2


class TestOutOfEnumEventTypeRejection:
    """Rows with missing or out-of-enum event_type should be rejected."""

    def test_blank_event_type_rejected(self):
        """Blank event_type is required and rejected."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': '',
            'gender': 'M',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_rejected'] == 1
        assert result['rows_normalized'] == 0
        assert 'event_type not in enum' in result['reject_reasons']

    def test_out_of_enum_event_type_rejected(self):
        """Unrecognized event_type value is rejected."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'unknown_type',
            'gender': 'M',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_rejected'] == 1
        assert len(result['reject_records']) == 1
        reject = result['reject_records'][0]
        assert 'event_type not in' in reject['__reject_reason']
        assert 'unknown_type' in reject['__reject_reason']


class TestGenderCoercion:
    """Gender should coerce, never reject."""

    def test_gender_recognized_value_normalizes(self):
        """Recognized gender values ('1', 'M', 'Female') normalize correctly."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': '1', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': 'F', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': 'Female', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 3
        assert result['rows_rejected'] == 0
        assert result['clean_records'][0]['gender'] == 'M'
        assert result['clean_records'][1]['gender'] == 'F'
        assert result['clean_records'][2]['gender'] == 'F'

    def test_gender_blank_coerces_to_u(self):
        """Blank gender coerces to 'U'."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': '',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        assert result['clean_records'][0]['gender'] == 'U'

    def test_gender_unrecognized_coerces_to_u(self):
        """Unrecognized gender value coerces to 'U' (not rejected)."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'X',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        assert result['rows_rejected'] == 0
        assert result['clean_records'][0]['gender'] == 'U'

    def test_gender_unrecognized_counts_as_coerced(self):
        """Unrecognized gender counted as coerced row."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'arrest',
            'gender': 'InvalidCode',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        assert result['rows_coerced'] == 1


class TestFieldTrimming:
    """field_office and removal_country should be trimmed."""

    def test_field_office_trimming(self):
        """Leading/trailing whitespace on field_office is trimmed."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': '  Boston  ',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['field_office'] == 'Boston'

    def test_removal_country_trimming(self):
        """Leading/trailing whitespace on removal_country is trimmed."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': '  Mexico  ',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['removal_country'] == 'Mexico'


class TestNationalityNormalization:
    """nationality should be upper-cased and trimmed."""

    def test_nationality_uppercase(self):
        """Nationality is converted to uppercase."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'mx',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['nationality'] == 'MX'

    def test_nationality_trimmed_and_uppercased(self):
        """Nationality is both trimmed and uppercased."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': '  mx  ',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['nationality'] == 'MX'


class TestRecordIdSynthesis:
    """record_id should be synthesized from source row index when absent/blank."""

    def test_record_id_synthesis_when_blank(self):
        """Blank record_id is synthesized from 1-based source row index."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['record_id'] == '1'

    def test_record_id_synthesis_index_progression(self):
        """Multiple rows synthesize record_id from their source index."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': 'M', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/16/2026', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/17/2026', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['record_id'] == '1'
        assert result['clean_records'][1]['record_id'] == '2'
        assert result['clean_records'][2]['record_id'] == '3'

    def test_record_id_preserved_when_present(self):
        """Non-blank record_id is preserved."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': '',
            'removal_country': '',
            'nationality': '',
            'record_id': 'existing-id',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['record_id'] == 'existing-id'


class TestCoercionCounting:
    """rows_coerced should count rows that underwent reformatting/mapping/substitution."""

    def test_coercion_counts_date_reformat(self):
        """Date reformatting counts as coercion."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 1

    def test_coercion_counts_event_type_code_mapping(self):
        """Event type code mapping counts as coercion."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'ARR',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 1

    def test_coercion_counts_field_office_trimming(self):
        """Field office trimming counts as coercion."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': '  Boston  ',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 1

    def test_coercion_counts_nationality_uppercasing(self):
        """Nationality uppercasing counts as coercion."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'mx',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 1

    def test_coercion_counts_record_id_synthesis(self):
        """record_id synthesis counts as coercion."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': '',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 1

    def test_no_coercion_when_all_canonical(self):
        """No coercion when all fields are already canonical."""
        rows = [{
            'event_date': '2026-01-15',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] == 0


class TestCountInvariants:
    """Verify count invariants and ordering."""

    def test_invariant_rows_ingested_equals_normalized_plus_rejected(self):
        """rows_ingested == rows_normalized + rows_rejected."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': 'M', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': 'invalid', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/16/2026', 'event_type': 'bad_type', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/17/2026', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_ingested'] == 4
        assert result['rows_normalized'] + result['rows_rejected'] == 4

    def test_invariant_rows_coerced_lte_rows_normalized(self):
        """rows_coerced <= rows_normalized."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': 'M', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/16/2026', 'event_type': 'arrest', 'gender': 'F', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': 'invalid', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_coerced'] <= result['rows_normalized']

    def test_reject_records_carry_original_row_data(self):
        """Rejected rows include all original row fields."""
        rows = [{
            'event_date': 'invalid',
            'event_type': 'arrest',
            'gender': 'M',
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        reject = result['reject_records'][0]
        assert reject['event_date'] == 'invalid'
        assert reject['event_type'] == 'arrest'
        assert reject['gender'] == 'M'
        assert reject['field_office'] == 'Boston'
        assert reject['__source_row'] == 1
        assert '__reject_reason' in reject

    def test_input_order_preserved(self):
        """Clean records preserve input row order."""
        rows = [
            {'event_date': '01/15/2026', 'event_type': 'arrest', 'gender': '1', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': 'a'},
            {'event_date': '01/16/2026', 'event_type': 'arrest', 'gender': '2', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': 'b'},
            {'event_date': '01/17/2026', 'event_type': 'arrest', 'gender': 'M', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': 'c'},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['record_id'] == 'a'
        assert result['clean_records'][1]['record_id'] == 'b'
        assert result['clean_records'][2]['record_id'] == 'c'


class TestColumnMapping:
    """Test behavior with various column mappings."""

    def test_column_mapping_with_aliases(self):
        """Different source headers map to canonical columns."""
        rows = [{
            'raw_date': '01/15/2026',
            'type_field': 'arrest',
            'sex': 'M',
            'office': 'Boston',
            'destination': 'Mexico',
            'nat': 'MX',
            'id': 'rec123',
        }]
        column_mapping = {
            'raw_date': 'event_date',
            'type_field': 'event_type',
            'sex': 'gender',
            'office': 'field_office',
            'destination': 'removal_country',
            'nat': 'nationality',
            'id': 'record_id',
        }

        result = normalize_rows([], rows, column_mapping)

        assert result['rows_normalized'] == 1
        clean_record = result['clean_records'][0]
        assert clean_record['event_date'] == '2026-01-15'
        assert clean_record['event_type'] == 'arrest'
        assert clean_record['gender'] == 'M'

    def test_missing_source_column_defaults_empty_string(self):
        """Missing source columns are treated as empty strings."""
        rows = [{
            'event_date': '01/15/2026',
            'event_type': 'arrest',
            # gender omitted
            'field_office': 'Boston',
            'removal_country': 'Mexico',
            'nationality': 'MX',
            'record_id': 'rec123',
        }]
        column_mapping = {
            'event_date': 'event_date',
            'event_type': 'event_type',
            'gender': 'gender',
            'field_office': 'field_office',
            'removal_country': 'removal_country',
            'nationality': 'nationality',
            'record_id': 'record_id',
        }

        result = normalize_rows([], rows, column_mapping)

        assert result['clean_records'][0]['gender'] == 'U'


class TestRejectionCategories:
    """Test rejection category tracking."""

    def test_reject_reasons_counter_tracks_categories(self):
        """reject_reasons Counter tracks rejection categories."""
        rows = [
            {'event_date': 'invalid', 'event_type': 'arrest', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/15/2026', 'event_type': '', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
            {'event_date': '01/15/2026', 'event_type': 'bad', 'gender': '', 'field_office': '', 'removal_country': '', 'nationality': '', 'record_id': ''},
        ]
        column_mapping = {col: col for col in rows[0].keys()}

        result = normalize_rows([], rows, column_mapping)

        assert result['reject_reasons']['unparseable event_date'] == 1
        assert result['reject_reasons']['event_type not in enum'] == 2

    def test_column_mappings_returned_in_result(self):
        """Result includes the column_mappings used."""
        rows = [{
            'raw_date': '01/15/2026',
            'type_field': 'arrest',
            'sex': 'M',
            'office': 'Boston',
            'destination': 'Mexico',
            'nat': 'MX',
            'id': 'rec123',
        }]
        column_mapping = {
            'raw_date': 'event_date',
            'type_field': 'event_type',
            'sex': 'gender',
            'office': 'field_office',
            'destination': 'removal_country',
            'nat': 'nationality',
            'id': 'record_id',
        }

        result = normalize_rows([], rows, column_mapping)

        assert result['column_mappings'] == column_mapping
