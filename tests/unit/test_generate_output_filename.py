"""
Unit tests for the generate_output_filename function
"""

from typing import Any, cast

from parse_visa_statement import generate_output_filename


class TestGenerateOutputFilename:
    """Test the generate_output_filename function"""

    def test_basic_filename_generation_bbva_visa(self):
        """Test basic filename generation for BBVA VISA"""
        result = generate_output_filename("BBVA VISA")
        assert result == "BBVA-VISA-transactions.xlsx"

    def test_basic_filename_generation_macro_visa(self):
        """Test basic filename generation for Macro VISA"""
        result = generate_output_filename("Macro VISA")
        assert result == "MACRO-VISA-transactions.xlsx"

    def test_basic_filename_generation_bbva_mastercard(self):
        """Test basic filename generation for BBVA Mastercard"""
        result = generate_output_filename("BBVA Mastercard")
        assert result == "BBVA-MASTERCARD-transactions.xlsx"

    def test_basic_filename_generation_bbva_account(self):
        """Test basic filename generation for BBVA Account"""
        result = generate_output_filename("BBVA Account")
        assert result == "BBVA-ACCOUNT-transactions.xlsx"

    def test_basic_filename_generation_macro_account(self):
        """Test basic filename generation for Macro Account"""
        result = generate_output_filename("Macro Account")
        assert result == "MACRO-ACCOUNT-transactions.xlsx"

    def test_basic_filename_generation_mercadopago(self):
        """Test basic filename generation for Mercadopago"""
        result = generate_output_filename("Mercadopago")
        assert result == "MERCADOPAGO-transactions.xlsx"

    def test_file_type_auth(self):
        """Test filename generation with auth file type"""
        result = generate_output_filename("BBVA VISA", file_type="auth")
        assert result == "BBVA-VISA-auth-transactions.xlsx"

    def test_file_type_movs(self):
        """Test filename generation with movs file type"""
        result = generate_output_filename("Macro VISA", file_type="movs")
        assert result == "MACRO-VISA-movs-transactions.xlsx"

    def test_file_type_main_explicit(self):
        """Test filename generation with explicit main file type"""
        result = generate_output_filename("BBVA VISA", file_type="main")
        assert result == "BBVA-VISA-transactions.xlsx"

    def test_date_inclusion_without_date_string(self):
        """Test date inclusion flag without providing date string"""
        result = generate_output_filename("BBVA VISA", include_date=True)
        assert result == "BBVA-VISA-transactions.xlsx"

    def test_date_inclusion_with_date_string(self):
        """Test date inclusion with date string"""
        result = generate_output_filename(
            "BBVA VISA", include_date=True, date_str="May-2025"
        )
        assert result == "BBVA-VISA-May-2025-transactions.xlsx"

    def test_date_inclusion_false_with_date_string(self):
        """Test date inclusion false even with date string provided"""
        result = generate_output_filename(
            "BBVA VISA", include_date=False, date_str="May-2025"
        )
        assert result == "BBVA-VISA-transactions.xlsx"

    def test_combined_file_type_and_date(self):
        """Test filename generation with both file type and date"""
        result = generate_output_filename(
            "BBVA VISA", file_type="auth", include_date=True, date_str="May-2025"
        )
        assert result == "BBVA-VISA-May-2025-auth-transactions.xlsx"

    def test_unknown_payment_method(self):
        """Test filename generation for unknown payment method"""
        result = generate_output_filename("Unknown Bank VISA")
        assert result == "UNKNOWN-BANK-VISA-transactions.xlsx"

    def test_unknown_payment_method_with_spaces(self):
        """Test filename generation for unknown payment method with multiple spaces"""
        result = generate_output_filename("Some New Bank Credit Card")
        assert result == "SOME-NEW-BANK-CREDIT-CARD-transactions.xlsx"

    def test_payment_method_mapping_coverage(self):
        """Test that all expected payment methods are properly mapped"""
        expected_mappings = {
            "BBVA VISA": "BBVA-VISA",
            "BBVA Mastercard": "BBVA-MASTERCARD",
            "BBVA Account": "BBVA-ACCOUNT",
            "Macro VISA": "MACRO-VISA",
            "Macro Account": "MACRO-ACCOUNT",
            "Mercadopago": "MERCADOPAGO",
        }

        for payment_method, expected_prefix in expected_mappings.items():
            result = generate_output_filename(payment_method)
            assert result == f"{expected_prefix}-transactions.xlsx"

    def test_case_sensitivity_handling(self):
        """Test that payment method case variations are handled correctly"""
        # Test different case variations
        variations = ["bbva visa", "BBVA VISA", "Bbva Visa", "BBVA visa"]

        # All should map to the same result for known methods
        for variation in variations:
            if variation.upper() == "BBVA VISA":
                result = generate_output_filename(variation)
                # Unknown variations will use the fallback logic
                expected = variation.upper().replace(" ", "-") + "-transactions.xlsx"
                assert result == expected

    def test_empty_date_string(self):
        """Test filename generation with empty date string"""
        result = generate_output_filename("BBVA VISA", include_date=True, date_str="")
        assert result == "BBVA-VISA-transactions.xlsx"

    def test_whitespace_date_string(self):
        """Test filename generation with whitespace-only date string"""
        result = generate_output_filename(
            "BBVA VISA", include_date=True, date_str="   "
        )
        assert result == "BBVA-VISA-   -transactions.xlsx"

    def test_special_characters_in_date(self):
        """Test filename generation with special characters in date"""
        result = generate_output_filename(
            "BBVA VISA", include_date=True, date_str="2025-05"
        )
        assert result == "BBVA-VISA-2025-05-transactions.xlsx"

    def test_multiple_file_types(self):
        """Test various file type combinations"""
        test_cases = [
            ("auth", "BBVA-VISA-auth-transactions.xlsx"),
            ("movs", "BBVA-VISA-movs-transactions.xlsx"),
            ("main", "BBVA-VISA-transactions.xlsx"),
            (
                "",
                "BBVA-VISA-transactions.xlsx",
            ),  # Empty string should be treated as main
        ]

        for file_type, expected in test_cases:
            result = generate_output_filename("BBVA VISA", file_type=file_type)
            assert result == expected

    def test_filename_extension_consistency(self):
        """Test that all generated filenames have .xlsx extension"""
        test_cases = [
            ("BBVA VISA", {}),
            ("Macro VISA", {"file_type": "auth"}),
            ("BBVA Account", {"include_date": True, "date_str": "2025"}),
            (
                "Unknown Method",
                {"file_type": "movs", "include_date": True, "date_str": "test"},
            ),
        ]

        for payment_method, kwargs in test_cases:
            result = generate_output_filename(
                payment_method, **cast(dict[str, Any], kwargs)
            )
            assert result.endswith(".xlsx")

    def test_component_order_consistency(self):
        """Test that filename components are always in the correct order"""
        result = generate_output_filename(
            "BBVA VISA", file_type="auth", include_date=True, date_str="May-2025"
        )

        # Expected order: BANK-PRODUCT-DATE-TYPE-transactions.xlsx
        assert result == "BBVA-VISA-May-2025-auth-transactions.xlsx"

        # Verify components are in correct positions
        parts = result.replace(".xlsx", "").split("-")
        assert parts[0] == "BBVA"
        assert parts[1] == "VISA"
        assert parts[2] == "May"
        assert parts[3] == "2025"
        assert parts[4] == "auth"
        assert parts[5] == "transactions"
