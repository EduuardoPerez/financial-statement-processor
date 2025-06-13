from parse_visa_statement import convert_date


class TestConvertDate:
    """Unit tests for the convert_date function"""

    def test_convert_date_2000s(self):
        """Test date conversion for 2000s years"""
        assert convert_date("01.12.22") == "2022-12-01"
        assert convert_date("15.06.23") == "2023-06-15"
        assert convert_date("31.01.00") == "2000-01-31"

    def test_convert_date_1900s(self):
        """Test date conversion for 1900s years"""
        assert convert_date("01.12.99") == "1999-12-01"
        assert convert_date("15.06.80") == "1980-06-15"
        assert convert_date("31.01.50") == "1950-01-31"

    def test_convert_date_padding(self):
        """Test that single digit days and months are padded"""
        assert convert_date("1.1.22") == "2022-01-01"
        assert convert_date("5.9.23") == "2023-09-05"

    def test_convert_date_mmm_format_2000s(self):
        """Test date conversion for DD-MMM-YY format (BBVA Mastercard) for 2000s years"""
        assert convert_date("15-Mar-25") == "2025-03-15"
        assert convert_date("27-Mar-25") == "2025-03-27"
        assert convert_date("04-Apr-25") == "2025-04-04"
        assert convert_date("01-Jan-00") == "2000-01-01"

    def test_convert_date_mmm_format_1900s(self):
        """Test date conversion for DD-MMM-YY format (BBVA Mastercard) for 1900s years"""
        assert convert_date("15-Mar-99") == "1999-03-15"
        assert convert_date("01-Dec-80") == "1980-12-01"
        assert convert_date("31-Jan-50") == "1950-01-31"

    def test_convert_date_spanish_month_abbreviations(self):
        """Test date conversion for Spanish month abbreviations (BBVA Mastercard)"""
        assert convert_date("04-Abr-25") == "2025-04-04"  # April in Spanish
        assert convert_date("15-Mar-25") == "2025-03-15"  # March
        assert convert_date("01-May-25") == "2025-05-01"  # May

    def test_convert_date_all_months_mmm_format(self):
        """Test date conversion for all month abbreviations in DD-MMM-YY format"""
        assert convert_date("01-Jan-25") == "2025-01-01"
        assert convert_date("01-Feb-25") == "2025-02-01"
        assert convert_date("01-Mar-25") == "2025-03-01"
        assert convert_date("01-Apr-25") == "2025-04-01"
        assert convert_date("01-Abr-25") == "2025-04-01"  # Spanish April
        assert convert_date("01-May-25") == "2025-05-01"
        assert convert_date("01-Jun-25") == "2025-06-01"
        assert convert_date("01-Jul-25") == "2025-07-01"
        assert convert_date("01-Aug-25") == "2025-08-01"
        assert convert_date("01-Sep-25") == "2025-09-01"
        assert convert_date("01-Oct-25") == "2025-10-01"
        assert convert_date("01-Nov-25") == "2025-11-01"
        assert convert_date("01-Dec-25") == "2025-12-01"
