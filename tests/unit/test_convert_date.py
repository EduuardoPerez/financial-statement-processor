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
