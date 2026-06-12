from deportation_foia_normalizer.dates import normalize_date


class TestFormatParsing:
    def test_mm_dd_yyyy_format(self):
        result = normalize_date('01/05/2026')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_m_d_yy_format(self):
        result = normalize_date('1/5/26')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_iso_passthrough(self):
        result = normalize_date('2026-01-05')
        assert result == {'date': '2026-01-05', 'coerced': False}

    def test_month_abbr_d_yyyy_format(self):
        result = normalize_date('Jan 5, 2026')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_month_full_d_yyyy_format(self):
        result = normalize_date('January 5, 2026')
        assert result == {'date': '2026-01-05', 'coerced': True}


class TestUnparseableInput:
    def test_invalid_date_impossible_day_month(self):
        result = normalize_date('32/13/2026')
        assert result is None

    def test_empty_string(self):
        result = normalize_date('')
        assert result is None

    def test_whitespace_only(self):
        result = normalize_date('   ')
        assert result is None


class TestCoercionFlag:
    def test_coercion_false_for_iso_passthrough(self):
        result = normalize_date('2026-06-11')
        assert result['coerced'] is False

    def test_coercion_true_for_reformatted(self):
        result = normalize_date('06/11/2026')
        assert result['coerced'] is True

    def test_coercion_true_for_month_format(self):
        result = normalize_date('June 11, 2026')
        assert result['coerced'] is True


class TestEdgeCases:
    def test_single_digit_month_and_day(self):
        result = normalize_date('1/1/2026')
        assert result == {'date': '2026-01-01', 'coerced': True}

    def test_two_digit_year_1900s(self):
        result = normalize_date('1/5/99')
        assert result == {'date': '1999-01-05', 'coerced': True}

    def test_two_digit_year_2000s(self):
        result = normalize_date('1/5/26')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_invalid_month_value(self):
        result = normalize_date('13/05/2026')
        assert result is None

    def test_invalid_day_value(self):
        result = normalize_date('01/32/2026')
        assert result is None

    def test_february_leap_year(self):
        result = normalize_date('02/29/2024')
        assert result == {'date': '2024-02-29', 'coerced': True}

    def test_february_non_leap_year(self):
        result = normalize_date('02/29/2023')
        assert result is None

    def test_month_abbr_case_insensitive(self):
        result = normalize_date('JAN 5, 2026')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_month_full_case_insensitive(self):
        result = normalize_date('JANUARY 5, 2026')
        assert result == {'date': '2026-01-05', 'coerced': True}

    def test_whitespace_trimmed(self):
        result = normalize_date('  01/05/2026  ')
        assert result == {'date': '2026-01-05', 'coerced': True}
