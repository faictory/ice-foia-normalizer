import pytest

from deportation_foia_normalizer.codes import normalize_gender, normalize_event_type
from deportation_foia_normalizer.record import GENDER_VALUES, EVENT_TYPE_VALUES


class TestNormalizeGender:
    """Unit tests for normalize_gender per DESIGN.md test expectations."""

    def test_gender_code_1_maps_to_m(self):
        """Gender code '1' normalizes to 'M' with coercion."""
        value, was_coerced = normalize_gender('1')
        assert value == 'M'
        assert was_coerced is True

    def test_gender_code_2_maps_to_f(self):
        """Gender code '2' normalizes to 'F' with coercion."""
        value, was_coerced = normalize_gender('2')
        assert value == 'F'
        assert was_coerced is True

    def test_gender_string_male_maps_to_m(self):
        """Gender string 'Male' normalizes to 'M' with coercion (case-fold)."""
        value, was_coerced = normalize_gender('Male')
        assert value == 'M'
        assert was_coerced is True

    def test_gender_string_male_lowercase(self):
        """Gender string 'male' normalizes to 'M' with coercion (case-fold)."""
        value, was_coerced = normalize_gender('male')
        assert value == 'M'
        assert was_coerced is True

    def test_gender_string_female_maps_to_f(self):
        """Gender string 'Female' normalizes to 'F' with coercion (case-fold)."""
        value, was_coerced = normalize_gender('Female')
        assert value == 'F'
        assert was_coerced is True

    def test_gender_string_female_lowercase(self):
        """Gender string 'female' normalizes to 'F' with coercion (case-fold)."""
        value, was_coerced = normalize_gender('female')
        assert value == 'F'
        assert was_coerced is True

    def test_gender_canonical_m_no_coercion(self):
        """Canonical 'M' returns with coercion=False (already canonical)."""
        value, was_coerced = normalize_gender('M')
        assert value == 'M'
        assert was_coerced is False

    def test_gender_canonical_f_no_coercion(self):
        """Canonical 'F' returns with coercion=False (already canonical)."""
        value, was_coerced = normalize_gender('F')
        assert value == 'F'
        assert was_coerced is False

    def test_gender_blank_string_maps_to_u(self):
        """Blank string normalizes to 'U' with coercion."""
        value, was_coerced = normalize_gender('')
        assert value == 'U'
        assert was_coerced is True

    def test_gender_whitespace_only_maps_to_u(self):
        """Whitespace-only string normalizes to 'U' with coercion."""
        value, was_coerced = normalize_gender('   ')
        assert value == 'U'
        assert was_coerced is True

    def test_gender_none_maps_to_u(self):
        """None normalizes to 'U' with coercion."""
        value, was_coerced = normalize_gender(None)
        assert value == 'U'
        assert was_coerced is True

    def test_gender_invalid_value_raises_valueerror(self):
        """Unrecognized gender value raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_gender('X')
        assert 'gender value not in' in str(exc_info.value)

    def test_gender_case_insensitive_m_lowercase(self):
        """Gender 'm' normalizes to 'M' with coercion."""
        value, was_coerced = normalize_gender('m')
        assert value == 'M'
        assert was_coerced is True

    def test_gender_case_insensitive_f_lowercase(self):
        """Gender 'f' normalizes to 'F' with coercion."""
        value, was_coerced = normalize_gender('f')
        assert value == 'F'
        assert was_coerced is True

    def test_gender_with_leading_trailing_whitespace(self):
        """Gender value with whitespace is trimmed before mapping."""
        value, was_coerced = normalize_gender('  M  ')
        assert value == 'M'
        assert was_coerced is False

    def test_gender_integer_coerces_to_string(self):
        """Integer gender code 1 is coerced to string and mapped."""
        value, was_coerced = normalize_gender(1)
        assert value == 'M'
        assert was_coerced is True


class TestNormalizeEventType:
    """Unit tests for normalize_event_type per DESIGN.md test expectations."""

    def test_event_type_code_arr_maps_to_arrest(self):
        """Event type code 'ARR' normalizes to 'arrest' with coercion."""
        value, was_coerced = normalize_event_type('ARR')
        assert value == 'arrest'
        assert was_coerced is True

    def test_event_type_code_arr_lowercase(self):
        """Event type code 'arr' normalizes to 'arrest' with coercion."""
        value, was_coerced = normalize_event_type('arr')
        assert value == 'arrest'
        assert was_coerced is True

    def test_event_type_code_det_maps_to_detainer(self):
        """Event type code 'DET' normalizes to 'detainer' with coercion."""
        value, was_coerced = normalize_event_type('DET')
        assert value == 'detainer'
        assert was_coerced is True

    def test_event_type_code_det_lowercase(self):
        """Event type code 'det' normalizes to 'detainer' with coercion."""
        value, was_coerced = normalize_event_type('det')
        assert value == 'detainer'
        assert was_coerced is True

    def test_event_type_code_rem_maps_to_removal(self):
        """Event type code 'REM' normalizes to 'removal' with coercion."""
        value, was_coerced = normalize_event_type('REM')
        assert value == 'removal'
        assert was_coerced is True

    def test_event_type_code_rem_lowercase(self):
        """Event type code 'rem' normalizes to 'removal' with coercion."""
        value, was_coerced = normalize_event_type('rem')
        assert value == 'removal'
        assert was_coerced is True

    def test_event_type_word_arrest_no_coercion(self):
        """Canonical word 'arrest' returns with coercion=False."""
        value, was_coerced = normalize_event_type('arrest')
        assert value == 'arrest'
        assert was_coerced is False

    def test_event_type_word_detainer_no_coercion(self):
        """Canonical word 'detainer' returns with coercion=False."""
        value, was_coerced = normalize_event_type('detainer')
        assert value == 'detainer'
        assert was_coerced is False

    def test_event_type_word_removal_no_coercion(self):
        """Canonical word 'removal' returns with coercion=False."""
        value, was_coerced = normalize_event_type('removal')
        assert value == 'removal'
        assert was_coerced is False

    def test_event_type_word_arrest_capitalized_coerces(self):
        """Capitalized 'Arrest' normalizes to 'arrest' with coercion."""
        value, was_coerced = normalize_event_type('Arrest')
        assert value == 'arrest'
        assert was_coerced is True

    def test_event_type_word_arrest_uppercase_coerces(self):
        """Uppercase 'ARREST' normalizes to 'arrest' with coercion."""
        value, was_coerced = normalize_event_type('ARREST')
        assert value == 'arrest'
        assert was_coerced is True

    def test_event_type_word_detainer_uppercase_coerces(self):
        """Uppercase 'DETAINER' normalizes to 'detainer' with coercion."""
        value, was_coerced = normalize_event_type('DETAINER')
        assert value == 'detainer'
        assert was_coerced is True

    def test_event_type_word_removal_uppercase_coerces(self):
        """Uppercase 'REMOVAL' normalizes to 'removal' with coercion."""
        value, was_coerced = normalize_event_type('REMOVAL')
        assert value == 'removal'
        assert was_coerced is True

    def test_event_type_with_leading_trailing_whitespace(self):
        """Event type value with whitespace is trimmed before mapping."""
        value, was_coerced = normalize_event_type('  arrest  ')
        assert value == 'arrest'
        assert was_coerced is False

    def test_event_type_blank_string_raises_valueerror(self):
        """Blank event type raises ValueError (required field)."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type('')
        assert 'event_type is required' in str(exc_info.value)

    def test_event_type_whitespace_only_raises_valueerror(self):
        """Whitespace-only event type raises ValueError (required field)."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type('   ')
        assert 'event_type is required' in str(exc_info.value)

    def test_event_type_none_raises_valueerror(self):
        """None event type raises ValueError (required field)."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type(None)
        assert 'event_type is required' in str(exc_info.value)

    def test_event_type_invalid_value_raises_valueerror(self):
        """Unrecognized event type value raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type('unknown')
        assert 'event_type not in' in str(exc_info.value)

    def test_event_type_invalid_code_raises_valueerror(self):
        """Invalid event type code raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type('XYZ')
        assert 'event_type not in' in str(exc_info.value)

    def test_event_type_integer_invalid_raises_valueerror(self):
        """Integer event type that doesn't map raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_event_type(1)
        assert 'event_type not in' in str(exc_info.value)


class TestCoercionSemantics:
    """Verify coercion flag semantics (case-fold, code-map, blank→U all count as coercion)."""

    def test_gender_case_fold_counts_as_coercion(self):
        """Case-folding of a valid value counts as coercion."""
        _, was_coerced = normalize_gender('MALE')
        assert was_coerced is True

    def test_gender_code_map_counts_as_coercion(self):
        """Code-mapping ('1' → 'M') counts as coercion."""
        _, was_coerced = normalize_gender('1')
        assert was_coerced is True

    def test_gender_blank_to_u_counts_as_coercion(self):
        """Blank-to-'U' substitution counts as coercion."""
        _, was_coerced = normalize_gender('')
        assert was_coerced is True

    def test_gender_exact_canonical_no_coercion(self):
        """Exact canonical value (no case change, no code map) has coercion=False."""
        _, was_coerced = normalize_gender('M')
        assert was_coerced is False

    def test_event_type_case_fold_counts_as_coercion(self):
        """Case-folding of a valid value counts as coercion."""
        _, was_coerced = normalize_event_type('ARREST')
        assert was_coerced is True

    def test_event_type_code_map_counts_as_coercion(self):
        """Code-mapping ('ARR' → 'arrest') counts as coercion."""
        _, was_coerced = normalize_event_type('ARR')
        assert was_coerced is True

    def test_event_type_exact_canonical_no_coercion(self):
        """Exact canonical value (no case change, no code map) has coercion=False."""
        _, was_coerced = normalize_event_type('arrest')
        assert was_coerced is False


class TestEnumValidation:
    """Verify that returned canonical values are valid enum members."""

    def test_gender_always_returns_valid_enum_member(self):
        """All returned gender values are in GENDER_VALUES."""
        test_inputs = ['1', '2', 'M', 'F', 'Male', 'Female', '', None]
        for raw in test_inputs:
            value, _ = normalize_gender(raw)
            assert value in GENDER_VALUES

    def test_event_type_always_returns_valid_enum_member(self):
        """All returned event_type values are in EVENT_TYPE_VALUES."""
        test_inputs = ['ARR', 'DET', 'REM', 'arrest', 'detainer', 'removal', 'Arrest']
        for raw in test_inputs:
            value, _ = normalize_event_type(raw)
            assert value in EVENT_TYPE_VALUES
