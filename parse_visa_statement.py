import pdfplumber
import pandas as pd
import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def detect_payment_method(full_text):
    """
    Detect payment method from PDF content
    Returns the payment method string (e.g., "Macro VISA", "BBVA VISA", "BBVA Mastercard")
    """
    text_upper = full_text.upper()

    # Check for Macro bank indicators first (more specific)
    macro_indicators = ["MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR"]
    macro_found = any(indicator in text_upper for indicator in macro_indicators)

    # Check for BBVA bank indicators (more specific than just VISA SIGNATURE)
    bbva_indicators = ["BBVA", "WWW.BBVA.COM.AR"]
    bbva_found = any(indicator in text_upper for indicator in bbva_indicators)

    # Check for card type indicators
    visa_found = "VISA" in text_upper
    mastercard_found = "MASTERCARD" in text_upper

    if macro_found and visa_found:
        return "Macro VISA"
    elif bbva_found and mastercard_found:
        return "BBVA Mastercard"
    elif bbva_found and visa_found:
        return "BBVA VISA"

    # Could add more bank/card combinations here in the future
    return "Unknown Payment Method"


def extract_balance_from_pdf(full_text, payment_method):
    """
    Extract reported balance from PDF text
    Returns dict with 'ars' and 'usd' balance amounts
    """
    balance = {"ars": 0.0, "usd": 0.0}

    if payment_method == "BBVA Mastercard":
        # BBVA Mastercard format: "SALDO ACTUAL $ 185.170,00 SALDO ACTUAL U$S 0,00"
        # or on same line: "30-Abr-25 09-May-25 185.170,00 0,00 30.853,00"
        pattern1 = r"SALDO ACTUAL \$ ([\d,.]+).*?SALDO ACTUAL U\$S ([\d,.]+)"
        match1 = re.search(pattern1, full_text)
        if match1:
            try:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            except:
                ars_str = "0"
                usd_str = "0"
        else:
            # Alternative pattern for BBVA Mastercard: find balance in the summary line
            pattern2 = r"\d{2}-\w{3}-\d{2}\s+\d{2}-\w{3}-\d{2}\s+([\d,.]+)\s+([\d,.]+)\s+[\d,.]+"
            match2 = re.search(pattern2, full_text)
            if match2:
                ars_str = match2.group(1)
                usd_str = match2.group(2)
            else:
                ars_str = "0"
                usd_str = "0"
    else:
        # Standard format for MACRO VISA and BBVA VISA: SALDO ACTUAL $ 1.095.461,57 U$S 3,00
        pattern = r"SALDO ACTUAL \$ ([\d,.]+) U\$S ([\d,.]+)"
        match = re.search(pattern, full_text)
        if match:
            ars_str = match.group(1)
            usd_str = match.group(2)
        else:
            ars_str = "0"
            usd_str = "0"

    try:
        # Handle European format for ARS: 1.095.461,57 -> 1095461.57
        if "." in ars_str and "," in ars_str:
            ars_str = ars_str.replace(".", "").replace(",", ".")
        elif "," in ars_str:
            ars_str = ars_str.replace(",", ".")

        # Handle European format for USD: 3,00 -> 3.00
        if "," in usd_str:
            usd_str = usd_str.replace(",", ".")

        balance["ars"] = float(ars_str)
        balance["usd"] = float(usd_str)
    except ValueError:
        pass

    return balance


def validate_balance(reported_balance, computed_balance, filename):
    """
    Validate computed totals against reported balance and log results
    """
    logger.info(f"[INFO] Validating balance for: {filename}")

    # Calculate differences
    ars_diff = reported_balance["ars"] - computed_balance["ars"]
    usd_diff = reported_balance["usd"] - computed_balance["usd"]

    # Format numbers with thousand separators for logging
    reported_ars = f"{reported_balance['ars']:,.2f}"
    computed_ars = f"{computed_balance['ars']:,.2f}"
    reported_usd = f"{reported_balance['usd']:,.2f}"
    computed_usd = f"{computed_balance['usd']:,.2f}"

    logger.info(
        f"        Reported ARS: {reported_ars} | "
        f"Computed ARS: {computed_ars} | Δ: {ars_diff:.2f}"
    )
    logger.info(
        f"        Reported USD: {reported_usd} | "
        f"Computed USD: {computed_usd} | Δ: {usd_diff:.2f}"
    )

    # Log warnings for mismatches (don't raise errors)
    if abs(ars_diff) > 0.01:  # Allow for small rounding differences
        logger.warning(
            f"[WARNING] ARS balance mismatch in {filename}: "
            f"difference of {ars_diff:.2f}"
        )

    if abs(usd_diff) > 0.01:
        logger.warning(
            f"[WARNING] USD balance mismatch in {filename}: "
            f"difference of {usd_diff:.2f}"
        )


def parse_visa_pdf(pdf_path, output_path):
    transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Detect payment method from PDF content
    payment_method = detect_payment_method(full_text)

    # Debug output removed - BBVA Mastercard processing is working correctly

    lines = full_text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Pattern for transaction lines with date
        date_pattern = r"(\d{2}\.\d{2}\.\d{2})\s+"
        date_pattern_mmm = (
            r"(\d{2}-\w{3}-\d{2})\s+"  # BBVA Mastercard format: 15-Mar-25
        )

        match = re.match(date_pattern, line)
        match_mmm = re.match(date_pattern_mmm, line)

        if match:
            date_str = match.group(1)
            remaining_line = line[match.end() :].strip()
        elif match_mmm:
            date_str = match_mmm.group(1)
            remaining_line = line[
                match_mmm.end() :
            ].strip()  # BBVA Mastercard single-line format
        else:
            continue

        if match or match_mmm:

            # Skip certain lines but handle specific cases
            if "SALDO ANTERIOR" in remaining_line or "Total Consumos" in remaining_line:
                continue

            # Handle BBVA Mastercard single-line format
            if payment_method == "BBVA Mastercard" and match_mmm:
                # Skip lines that don't look like transactions
                if (
                    len(remaining_line.split()) < 2
                    or "SALDO ACTUAL" in remaining_line
                    or "VENCIMIENTO" in remaining_line
                    or remaining_line.count("-") > 2
                    or "PAGO MÍNIMO" in remaining_line
                    or re.match(
                        r"\d{2}-\w{3}-\d{2}\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+",
                        remaining_line,
                    )  # Skip balance lines like "09-May-25 185.170,00 0,00 30.853,00"
                ):  # Skip date range lines like "04-Abr-25 29-May-25 06-Jun-"
                    continue

                # For BBVA Mastercard, format is: DD-MMM-YY DESCRIPTION REFERENCE AMOUNT
                if "SU PAGO EN PESOS" in remaining_line:
                    # Extract amount from payment line (could be negative already)
                    amount_match = re.search(r"(-?[\d,.]+)$", remaining_line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        # Handle negative sign
                        is_negative = amount_str.startswith("-")
                        if is_negative:
                            amount_str = amount_str[1:]  # Remove the negative sign

                        # Convert European format
                        if "." in amount_str and "," in amount_str:
                            amount_str = amount_str.replace(".", "").replace(",", ".")
                        elif "," in amount_str:
                            amount_str = amount_str.replace(",", ".")
                        try:
                            amount = -float(amount_str)  # Always negative for payments
                            transaction = {
                                "Date": convert_date(date_str),
                                "Description": "SU PAGO EN PESOS",
                                "Currency": "ARS",
                                "Amount": amount,
                                "Payment Method": payment_method,
                            }
                            transactions.append(transaction)
                        except ValueError:
                            pass
                else:
                    # Regular transaction: extract amount from end and description from middle
                    amount_match = re.search(r"([\d,.]+)$", remaining_line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        # Convert European format
                        if "." in amount_str and "," in amount_str:
                            amount_str = amount_str.replace(".", "").replace(",", ".")
                        elif "," in amount_str:
                            amount_str = amount_str.replace(",", ".")
                        try:
                            amount = float(amount_str)
                            # Extract description (everything except the amount)
                            description = remaining_line.rsplit(
                                amount_match.group(1), 1
                            )[0].strip()
                            # Skip if description looks like balance info
                            if len(description.split()) < 2:
                                continue
                            transaction = {
                                "Date": convert_date(date_str),
                                "Description": description,
                                "Currency": "ARS",
                                "Amount": amount,
                                "Payment Method": payment_method,
                            }
                            transactions.append(transaction)
                        except ValueError:
                            pass
                continue

            # Handle tax entries (IMPUESTO, IIBB, IVA, DB.RG, DB.IMPUESTO)
            if any(
                tax in remaining_line
                for tax in [
                    "IMPUESTO DE SELLOS",
                    "DB.IMPUESTO PAIS",
                    "IIBB PERCEP",
                    "IVA RG",
                    "DB.RG",
                ]
            ):
                # Extract amount from tax lines with European format support
                amount_match = re.search(r"([\d.,]+)$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Handle European format: 6.847,70 -> 6847.70
                    if "." in amount_str and "," in amount_str:
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    elif "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = float(amount_str)
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": remaining_line.rsplit(
                                amount_match.group(1), 1
                            )[0].strip(),
                            "Currency": "ARS",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle payment lines (SU PAGO EN PESOS)
            if "SU PAGO EN PESOS" in remaining_line:
                # Handle format like "SU PAGO EN PESOS 701.084,93-"
                amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Convert European format
                    if "." in amount_str and "," in amount_str:
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    elif "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = -float(amount_str)  # Always negative for payments
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": "SU PAGO EN PESOS",
                            "Currency": "ARS",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle USD payment lines (SU PAGO EN USD)
            if "SU PAGO EN USD" in remaining_line:
                # Handle format like "SU PAGO EN USD 3,00-"
                amount_match = re.search(r"([\d,.]+)-?\s*_?$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Convert European format for USD amounts
                    if "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = -float(amount_str)  # Always negative for payments
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": "SU PAGO EN USD",
                            "Currency": "USD",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle adjustment lines
            if "AJUSTE" in remaining_line:
                # Handle format like "AJUSTE P/DESCNTO. EN COMERCIO 1.200,00-"
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Convert European format
                    if "." in amount_str and "," in amount_str:
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    elif "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = -float(amount_str)  # Always negative for adjustments
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": "AJUSTE P/DESCNTO. EN COMERCIO",
                            "Currency": "ARS",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle BBVA bonification lines (BONIF.)
            if "BONIF." in remaining_line:
                # Handle format like "BONIF. CONSUMO CABIFY25169EPTMFAA 1.190,07-"
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Convert European format
                    if "." in amount_str and "," in amount_str:
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    elif "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = -float(amount_str)  # Always negative for bonifications
                        description = remaining_line.rsplit(amount_match.group(0), 1)[
                            0
                        ].strip()
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": description,
                            "Currency": "ARS",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Handle OFF/promo lines (similar to bonifications)
            if "OFF " in remaining_line or "Promo" in remaining_line:
                # Handle format like "OFF Promo Visa Subtes 304,15-"
                amount_match = re.search(r"([\d,.]+)-?\s*$", remaining_line)
                if amount_match:
                    amount_str = amount_match.group(1)
                    # Convert European format
                    if "." in amount_str and "," in amount_str:
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    elif "," in amount_str:
                        amount_str = amount_str.replace(",", ".")
                    try:
                        amount = -float(amount_str)  # Always negative for promos
                        description = remaining_line.rsplit(amount_match.group(0), 1)[
                            0
                        ].strip()
                        transaction = {
                            "Date": convert_date(date_str),
                            "Description": description,
                            "Currency": "ARS",
                            "Amount": amount,
                            "Payment Method": payment_method,
                        }
                        transactions.append(transaction)
                    except ValueError:
                        continue
                continue

            # Parse regular transactions - more flexible approach
            # Look for reference number pattern at start
            ref_match = re.match(r"([A-Z0-9*]+[*KQV]?)\s+", remaining_line)

            if ref_match:
                ref_number = ref_match.group(1)
                after_ref = remaining_line[ref_match.end() :].strip()

                # Check for USD transactions
                usd_match = re.search(r"USD\s+([\d,.-]+)", after_ref)
                if usd_match:
                    amount = float(usd_match.group(1).replace(",", "."))
                    desc_before_usd = after_ref.split("USD")[0].strip()
                    # Include USD amount in description to match expected format
                    usd_amount_str = usd_match.group(1)
                    transaction = {
                        "Date": convert_date(date_str),
                        "Description": f"{ref_number} {desc_before_usd} USD {usd_amount_str}".strip(),
                        "Currency": "USD",
                        "Amount": amount,
                        "Payment Method": payment_method,
                    }
                    transactions.append(transaction)
                    continue

                # For ARS transactions, find amount at the end
                # Handle European format: 1.234,56 or simple formats
                amount_patterns = [
                    r"(\d{1,3}(?:\.\d{3})*,\d{2})$",  # 1.234,56 format
                    r"(\d+,\d{2})$",  # 123,45 format
                    r"(\d+\.\d{2})$",  # 123.45 format (US style)
                    r"(\d+)$",  # Integer amounts
                ]

                amount_found = False
                for pattern in amount_patterns:
                    amount_match = re.search(pattern, after_ref)
                    if amount_match:
                        amount_str = amount_match.group(1)

                        # Convert European format to standard decimal
                        if "." in amount_str and "," in amount_str:
                            # Format like 1.234,56 -> remove dots, convert comma to dot
                            amount_str = amount_str.replace(".", "").replace(",", ".")
                        elif "," in amount_str and len(amount_str.split(",")[1]) == 2:
                            # Format like 1234,56 -> convert comma to dot
                            amount_str = amount_str.replace(",", ".")

                        try:
                            amount = float(amount_str)
                            # Extract description without amount
                            description = after_ref.rsplit(amount_match.group(1), 1)[
                                0
                            ].strip()
                            full_description = f"{ref_number} {description}".strip()

                            transaction = {
                                "Date": convert_date(date_str),
                                "Description": full_description,
                                "Currency": "ARS",
                                "Amount": amount,
                                "Payment Method": payment_method,
                            }
                            transactions.append(transaction)
                            amount_found = True
                            break
                        except ValueError:
                            continue

                if not amount_found:
                    # Fallback: try to find all numbers and use the most likely amount
                    # Look for patterns that include both dots and commas (European format)
                    european_amounts = re.findall(
                        r"\d{1,3}(?:\.\d{3})*,\d{2}", after_ref
                    )
                    if european_amounts:
                        amount_str = (
                            european_amounts[-1].replace(".", "").replace(",", ".")
                        )
                        try:
                            amount = float(amount_str)
                            description = after_ref.replace(
                                european_amounts[-1], ""
                            ).strip()
                            full_description = f"{ref_number} {description}".strip()

                            transaction = {
                                "Date": convert_date(date_str),
                                "Description": full_description,
                                "Currency": "ARS",
                                "Amount": amount,
                                "Payment Method": payment_method,
                            }
                            transactions.append(transaction)
                            continue
                        except ValueError:
                            pass

                    # Last resort: find any number-like pattern
                    numbers = re.findall(r"[\d,.-]+", after_ref)
                    if numbers:
                        # Try to find the best candidate for amount (typically at the end)
                        for num in reversed(numbers):
                            try:
                                # Simple conversion - assume comma is decimal separator if 2 digits after
                                if "," in num and len(num.split(",")[-1]) == 2:
                                    amount_str = num.replace(".", "").replace(",", ".")
                                else:
                                    amount_str = num.replace(",", "")

                                amount = float(amount_str)
                                if (
                                    amount > 0
                                ):  # Only positive amounts for regular transactions
                                    description = after_ref.replace(num, "").strip()
                                    full_description = (
                                        f"{ref_number} {description}".strip()
                                    )

                                    transaction = {
                                        "Date": convert_date(date_str),
                                        "Description": full_description,
                                        "Currency": "ARS",
                                        "Amount": amount,
                                        "Payment Method": payment_method,
                                    }
                                    transactions.append(transaction)
                                    break
                            except ValueError:
                                continue

    # Convert to DataFrame and save
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Extract balance from PDF and validate
    reported_balance = extract_balance_from_pdf(full_text, payment_method)

    # Calculate computed balance (excluding payments)
    # ARS: sum all ARS transactions except "SU PAGO EN PESOS"
    ars_transactions = df[df["Currency"] == "ARS"]
    ars_non_payments = ars_transactions[
        ars_transactions["Description"] != "SU PAGO EN PESOS"
    ]
    computed_ars_total = ars_non_payments["Amount"].sum()

    # USD: sum all USD transactions except "SU PAGO EN USD"
    usd_transactions = df[df["Currency"] == "USD"]
    usd_non_payments = usd_transactions[
        usd_transactions["Description"] != "SU PAGO EN USD"
    ]
    computed_usd_total = usd_non_payments["Amount"].sum()

    computed_balance = {"ars": computed_ars_total, "usd": computed_usd_total}

    # Validate balance
    filename = os.path.basename(pdf_path)
    validate_balance(reported_balance, computed_balance, filename)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def convert_date(date_str):
    """Convert DD.MM.YY or DD-MMM-YY to YYYY-MM-DD format"""
    if "-" in date_str:
        # Handle DD-MMM-YY format (BBVA Mastercard)
        day, month_name, year = date_str.split("-")
        month_map = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "Abr": "04",  # Spanish abbreviation for April
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        month = month_map.get(month_name, "01")
    else:
        # Handle DD.MM.YY format (MACRO VISA, BBVA VISA)
        day, month, year = date_str.split(".")

    # Assuming years < 50 = 20XX, years >= 50 = 19XX
    if int(year) < 50:
        full_year = 2000 + int(year)
    else:
        full_year = 1900 + int(year)

    return f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"


def print_processing_summary(
    filename, df, reported_balance, computed_balance, output_path
):
    """Print organized summary of processing results"""
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY: {filename}")
    print(f"{'='*60}")
    print(f"Transactions Processed: {len(df)}")
    print(f"Output File: {output_path}")

    # Calculate totals including payments
    total_ars = df[df["Currency"] == "ARS"]["Amount"].sum()
    total_usd = df[df["Currency"] == "USD"]["Amount"].sum()

    print(f"\nACTUAL TOTALS (including payments):")
    print(f"  ARS: {total_ars:,.2f}")
    print(f"  USD: {total_usd:.2f}")

    print(f"\nBALANCE VALIDATION:")
    print(f"  Reported ARS: {reported_balance['ars']:,.2f}")
    print(f"  Computed ARS: {computed_balance['ars']:,.2f}")
    print(
        f"  ARS Match: {'✅ YES' if abs(reported_balance['ars'] - computed_balance['ars']) < 0.01 else '❌ NO'}"
    )

    print(f"  Reported USD: {reported_balance['usd']:,.2f}")
    print(f"  Computed USD: {computed_balance['usd']:,.2f}")
    print(
        f"  USD Match: {'✅ YES' if abs(reported_balance['usd'] - computed_balance['usd']) < 0.01 else '❌ NO'}"
    )


if __name__ == "__main__":
    results = []

    # Process Macro VISA statement
    print("Processing Macro VISA statement...")
    input_file = "input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"
    output_file = "output/MACRO-VISA-transactions.xlsx"
    df_macro = parse_visa_pdf(input_file, output_file)

    # Get validation data for summary
    with pdfplumber.open(input_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    payment_method = detect_payment_method(full_text)
    reported_macro = extract_balance_from_pdf(full_text, payment_method)

    ars_non_payments = df_macro[
        (df_macro["Currency"] == "ARS")
        & (df_macro["Description"] != "SU PAGO EN PESOS")
    ]
    usd_non_payments = df_macro[
        (df_macro["Currency"] == "USD") & (df_macro["Description"] != "SU PAGO EN USD")
    ]
    computed_macro = {
        "ars": ars_non_payments["Amount"].sum(),
        "usd": usd_non_payments["Amount"].sum(),
    }

    results.append(
        (
            "MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf",
            df_macro,
            reported_macro,
            computed_macro,
            output_file,
        )
    )

    # Process BBVA VISA statement
    print("Processing BBVA VISA statement...")
    input_file = "input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"
    output_file = "output/BBVA-VISA-transactions.xlsx"
    df_bbva = parse_visa_pdf(input_file, output_file)

    # Get validation data for summary
    with pdfplumber.open(input_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    payment_method = detect_payment_method(full_text)
    reported_bbva = extract_balance_from_pdf(full_text, payment_method)

    ars_non_payments = df_bbva[
        (df_bbva["Currency"] == "ARS") & (df_bbva["Description"] != "SU PAGO EN PESOS")
    ]
    usd_non_payments = df_bbva[
        (df_bbva["Currency"] == "USD") & (df_bbva["Description"] != "SU PAGO EN USD")
    ]
    computed_bbva = {
        "ars": ars_non_payments["Amount"].sum(),
        "usd": usd_non_payments["Amount"].sum(),
    }

    results.append(
        (
            "BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf",
            df_bbva,
            reported_bbva,
            computed_bbva,
            output_file,
        )
    )

    # Process BBVA Mastercard statement
    print("Processing BBVA Mastercard statement...")
    input_file = "input/BBVA-Mastercard-2025-04.pdf"
    output_file = "output/BBVA-Mastercard-transactions.xlsx"
    df_bbva_mc = parse_visa_pdf(input_file, output_file)

    # Get validation data for summary
    with pdfplumber.open(input_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    payment_method = detect_payment_method(full_text)
    reported_bbva_mc = extract_balance_from_pdf(full_text, payment_method)

    ars_non_payments = df_bbva_mc[
        (df_bbva_mc["Currency"] == "ARS")
        & (df_bbva_mc["Description"] != "SU PAGO EN PESOS")
    ]
    usd_non_payments = df_bbva_mc[
        (df_bbva_mc["Currency"] == "USD")
        & (df_bbva_mc["Description"] != "SU PAGO EN USD")
    ]
    computed_bbva_mc = {
        "ars": ars_non_payments["Amount"].sum(),
        "usd": usd_non_payments["Amount"].sum(),
    }

    results.append(
        (
            "BBVA-Mastercard-2025-04.pdf",
            df_bbva_mc,
            reported_bbva_mc,
            computed_bbva_mc,
            output_file,
        )
    )

    # Print organized summary for all files
    for filename, df, reported, computed, output_path in results:
        print_processing_summary(filename, df, reported, computed, output_path)

    print(f"\n{'='*60}")
    print("ALL PROCESSING COMPLETE")
    print(f"{'='*60}")
