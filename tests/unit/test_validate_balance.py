import logging

from parse_visa_statement import validate_balance


class TestValidateBalance:
    """Unit tests for the validate_balance function"""

    def test_validate_balance_match(self, caplog):
        """Test balance validation when balances match"""
        reported = {"ars": 1000.50, "usd": 25.75}
        computed = {"ars": 1000.50, "usd": 25.75}
        filename = "test_statement.pdf"

        with caplog.at_level(logging.INFO):
            validate_balance(reported, computed, filename)

        assert "[INFO] Validating balance for: test_statement.pdf" in caplog.text
        assert "Reported ARS: 1,000.50" in caplog.text
        assert "Computed ARS: 1,000.50" in caplog.text
        assert "Reported USD: 25.75" in caplog.text
        assert "Computed USD: 25.75" in caplog.text

    def test_validate_balance_ars_mismatch(self, caplog):
        """Test balance validation when ARS balance doesn't match"""
        reported = {"ars": 1000.50, "usd": 25.75}
        computed = {"ars": 1000.00, "usd": 25.75}
        filename = "test_statement.pdf"

        with caplog.at_level(logging.WARNING):
            validate_balance(reported, computed, filename)

        assert "[WARNING] ARS balance mismatch in test_statement.pdf" in caplog.text
        assert "difference of 0.50" in caplog.text

    def test_validate_balance_usd_mismatch(self, caplog):
        """Test balance validation when USD balance doesn't match"""
        reported = {"ars": 1000.50, "usd": 25.75}
        computed = {"ars": 1000.50, "usd": 25.25}
        filename = "test_statement.pdf"

        with caplog.at_level(logging.WARNING):
            validate_balance(reported, computed, filename)

        assert "[WARNING] USD balance mismatch in test_statement.pdf" in caplog.text
        assert "difference of 0.50" in caplog.text

    def test_validate_balance_both_mismatch(self, caplog):
        """Test balance validation when both balances don't match"""
        reported = {"ars": 1000.50, "usd": 25.75}
        computed = {"ars": 999.50, "usd": 24.75}
        filename = "test_statement.pdf"

        with caplog.at_level(logging.WARNING):
            validate_balance(reported, computed, filename)

        assert "[WARNING] ARS balance mismatch in test_statement.pdf" in caplog.text
        assert "difference of 1.00" in caplog.text
        assert "[WARNING] USD balance mismatch in test_statement.pdf" in caplog.text
        assert "difference of 1.00" in caplog.text

    def test_validate_balance_small_difference(self, caplog):
        """Test that small differences (< 0.01) don't trigger warnings"""
        reported = {"ars": 1000.505, "usd": 25.754}
        computed = {"ars": 1000.500, "usd": 25.750}
        filename = "test_statement.pdf"

        with caplog.at_level(logging.WARNING):
            validate_balance(reported, computed, filename)

        # Should not contain warning messages for small differences
        assert "[WARNING]" not in caplog.text

    def test_validate_balance_zero_amounts(self, caplog):
        """Test balance validation with zero amounts"""
        reported = {"ars": 0.0, "usd": 0.0}
        computed = {"ars": 0.0, "usd": 0.0}
        filename = "zero_balance.pdf"

        with caplog.at_level(logging.INFO):
            validate_balance(reported, computed, filename)

        assert "Reported ARS: 0.00" in caplog.text
        assert "Computed ARS: 0.00" in caplog.text
        assert "Δ: 0.00" in caplog.text

    def test_validate_balance_large_numbers(self, caplog):
        """Test balance validation with large numbers"""
        reported = {"ars": 10000000.99, "usd": 50000.25}
        computed = {"ars": 10000000.99, "usd": 50000.25}
        filename = "large_balance.pdf"

        with caplog.at_level(logging.INFO):
            validate_balance(reported, computed, filename)

        assert "Reported ARS: 10,000,000.99" in caplog.text
        assert "Computed ARS: 10,000,000.99" in caplog.text
        assert "Reported USD: 50,000.25" in caplog.text
        assert "Computed USD: 50,000.25" in caplog.text
