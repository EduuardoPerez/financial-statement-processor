from parse_visa_statement import extract_balance_from_pdf


class TestExtractBalanceFromPdf:
    """Unit tests for the extract_balance_from_pdf function"""

    def test_extract_balance_normal_format(self):
        """Test extraction of balance with normal format"""
        text = "Some text\nSALDO ACTUAL $ 1.095.461,57 U$S 3,00\nMore text"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 1095461.57
        assert result["usd"] == 3.00

    def test_extract_balance_simple_format(self):
        """Test extraction of balance with simple format (no thousands separator)"""
        text = "Some text\nSALDO ACTUAL $ 123,45 U$S 10,50\nMore text"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 123.45
        assert result["usd"] == 10.50

    def test_extract_balance_zero_values(self):
        """Test extraction of balance with zero values"""
        text = "Some text\nSALDO ACTUAL $ 0,00 U$S 0,00\nMore text"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 0.0
        assert result["usd"] == 0.0

    def test_extract_balance_no_pattern_match(self):
        """Test when balance pattern is not found"""
        text = "Some text without balance information"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 0.0
        assert result["usd"] == 0.0

    def test_extract_balance_invalid_ars_number(self):
        """Test with invalid ARS number format that causes ValueError"""
        text = "SALDO ACTUAL $ invalid.number,57 U$S 3,00"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 0.0
        assert result["usd"] == 0.0

    def test_extract_balance_invalid_usd_number(self):
        """Test with invalid USD number format that causes ValueError"""
        text = "SALDO ACTUAL $ 1.095.461,57 U$S invalid"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 0.0
        assert result["usd"] == 0.0

    def test_extract_balance_only_comma_separator(self):
        """Test balance extraction with only comma as decimal separator"""
        text = "SALDO ACTUAL $ 12345,67 U$S 89,01"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 12345.67
        assert result["usd"] == 89.01

    def test_extract_balance_large_numbers(self):
        """Test balance extraction with very large numbers"""
        text = "SALDO ACTUAL $ 10.000.000,99 U$S 50000,25"
        result = extract_balance_from_pdf(text, "Test Bank")
        assert result["ars"] == 10000000.99
        assert result["usd"] == 50000.25

    def test_extract_balance_bbva_mastercard_format(self):
        """Test balance extraction for BBVA Mastercard specific format"""
        text = "30-Abr-25 09-May-25 185.170,00 0,00 30.853,00"
        result = extract_balance_from_pdf(text, "BBVA Mastercard")
        assert result["ars"] == 185170.00
        assert result["usd"] == 0.00

    def test_extract_balance_bbva_mastercard_fallback_pattern(self):
        """Test BBVA Mastercard balance extraction when primary pattern fails"""
        text = "Some other text without direct balance"
        result = extract_balance_from_pdf(text, "BBVA Mastercard")
        assert result["ars"] == 0.0
        assert result["usd"] == 0.0
