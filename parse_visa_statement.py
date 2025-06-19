from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

import pandas as pd
import pdfplumber

if TYPE_CHECKING:
    from pandas import DataFrame

# Type aliases for better code readability
Transaction = dict[str, str | float]
BalanceDict = dict[str, float]
ValidationResult = dict[str, float]

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def detect_payment_method(
    content_or_path: str | None = None,
    file_path: str | None = None,
    full_text: str | None = None,
) -> str:
    """
    Detect payment method from PDF content or filename
    Returns the payment method string (e.g., "Macro VISA", "BBVA VISA",
    "BBVA Mastercard", "BBVA Account")

    For backwards compatibility, accepts content as first positional argument
    """
    # Handle backwards compatibility - if first argument is provided, treat as full_text
    if content_or_path is not None and full_text is None and file_path is None:
        full_text = content_or_path
    elif content_or_path is not None and file_path is None:
        file_path = content_or_path

    # For XLS/XLSX files, detect based on filename
    if file_path and file_path.lower().endswith((".xls", ".xlsx")):
        filename_upper = os.path.basename(file_path).upper()
        if all(keyword in filename_upper for keyword in ["BBVA", "DETALLE"]) or all(
            keyword in filename_upper for keyword in ["BBVA", "ACCOUNT"]
        ):
            return "BBVA Account"
        elif all(keyword in filename_upper for keyword in ["MACRO", "MOVIMIENTOS"]):
            return "Macro Account"
        elif "MERCADOPAGO" in filename_upper:
            return "Mercadopago"

    # For CSV files, detect based on filename
    if file_path and file_path.lower().endswith(".csv"):
        filename_upper = os.path.basename(file_path).upper()
        if all(keyword in filename_upper for keyword in ["BBVA", "VISA"]):
            return "BBVA VISA"
        elif all(keyword in filename_upper for keyword in ["MACRO", "VISA"]):
            return "Macro VISA"

    # For PDF files, detect based on content
    if full_text:
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


def extract_balance_from_pdf(full_text: str, payment_method: str) -> BalanceDict:
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
            except (AttributeError, IndexError):
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


def validate_balance(
    reported_balance: BalanceDict, computed_balance: BalanceDict, filename: str
) -> None:
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


def parse_visa_pdf(pdf_path: str, output_path: str) -> DataFrame:
    transactions: list[Transaction] = []

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Detect payment method from PDF content
    payment_method = detect_payment_method(full_text=full_text)

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

    # Handle empty DataFrame case
    if len(df) > 0:
        # Sort by date to match expected output
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Extract balance from PDF and validate
    reported_balance = extract_balance_from_pdf(full_text, payment_method)

    # Calculate computed balance (excluding payments)
    if len(df) > 0:
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
    else:
        computed_ars_total = 0.0
        computed_usd_total = 0.0

    computed_balance = {"ars": computed_ars_total, "usd": computed_usd_total}

    # Validate balance
    filename = os.path.basename(pdf_path)
    validate_balance(reported_balance, computed_balance, filename)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def parse_account_xls(xls_path: str, output_path: str) -> DataFrame:
    """
    Parse BBVA Account XLS file and generate Excel output
    """
    transactions = []

    # Read the XLS file
    df = pd.read_excel(xls_path)

    # Skip header rows (row 0 is title, row 1 is column headers) and get actual data
    data_rows = df.iloc[2:]  # Start from row 2 (third row)

    # Filter valid transaction rows
    for _, row in data_rows.iterrows():
        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[3]):  # Date and Amount not null
            fecha_str = str(row.iloc[0]).strip()
            concepto_str = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            importe_str = str(row.iloc[3]).strip()

            if fecha_str and importe_str and importe_str != "nan":
                # Convert date from DD/MM/YYYY to YYYY-MM-DD
                try:
                    # Handle dates like "09/06/2025"
                    day, month, year = fecha_str.split("/")
                    formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue  # Skip invalid dates

                # Convert amount from European format to float
                try:
                    # Handle European format: -28.820,00 -> -28820.00
                    amount_str = importe_str.replace(".", "").replace(",", ".")
                    amount = float(amount_str)
                except ValueError:
                    continue  # Skip invalid amounts

                transaction = {
                    "Date": formatted_date,
                    "Description": concepto_str,
                    "Currency": "ARS",  # BBVA Account transactions are in ARS
                    "Amount": amount,
                    "Payment Method": "BBVA Account",
                }
                transactions.append(transaction)

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output (descending - newest first)
    if len(df) > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date", ascending=False)
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def parse_macro_account_xls(xls_path, output_path):
    """
    Parse Macro Account XLS file and generate Excel output
    """
    transactions = []

    # Read the XLS file
    df = pd.read_excel(xls_path, header=None)

    # Skip header rows (row 0 is title, row 1 is account number, row 2 is column headers)
    data_rows = df.iloc[3:]  # Start from row 3 (fourth row)

    # Filter valid transaction rows
    for _, row in data_rows.iterrows():
        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[3]):  # Date and Amount not null
            fecha = row.iloc[0]  # Already a datetime object
            descripcion = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            importe = row.iloc[3]  # Already a number

            if fecha and pd.notna(importe):
                # Convert datetime to YYYY-MM-DD format
                formatted_date = fecha.strftime("%Y-%m-%d")

                # Amount is already in proper numeric format
                amount = float(importe)

                transaction = {
                    "Date": formatted_date,
                    "Description": descripcion,
                    "Currency": "ARS",  # Macro Account transactions are in ARS
                    "Amount": amount,
                    "Payment Method": "Macro Account",
                }
                transactions.append(transaction)

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output (descending - newest first)
    if len(df) > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date", ascending=False)
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def parse_bbva_visa_csv(csv_path, output_path, file_type):
    """
    Parse BBVA VISA CSV file (Autorizaciones or Movimientos) and generate Excel output
    """
    transactions = []

    # Read the CSV file with semicolon separator
    df = pd.read_csv(csv_path, sep=";")

    # Process each row
    for _, row in df.iterrows():
        # Handle different date column names between file types
        if file_type == "movs":
            fecha_str = (
                str(row["Fecha Origen"]).strip()
                if pd.notna(row["Fecha Origen"])
                else ""
            )
        else:
            fecha_str = str(row["Fecha"]).strip() if pd.notna(row["Fecha"]) else ""

        establecimiento = (
            str(row["Establecimiento"]).strip()
            if pd.notna(row["Establecimiento"])
            else ""
        )
        moneda = str(row["Moneda"]).strip() if pd.notna(row["Moneda"]) else ""
        importe_str = str(row["Importe"]).strip() if pd.notna(row["Importe"]) else ""

        if fecha_str and importe_str and importe_str != "nan":
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            try:
                day, month, year = fecha_str.split("/")
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                continue  # Skip invalid dates

            # Convert amount from European format to float
            try:
                # Handle European format: 4,940.00 -> 4940.00
                amount_str = importe_str.replace(",", "")
                amount = float(amount_str)
            except ValueError:
                continue  # Skip invalid amounts

            # Map currency
            currency = (
                "ARS" if moneda == "Pesos" else "USD" if moneda == "Dolares" else "ARS"
            )

            transaction = {
                "Date": formatted_date,
                "Description": establecimiento,
                "Currency": currency,
                "Amount": amount,
                "Payment Method": "BBVA VISA",
            }
            transactions.append(transaction)

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output
    if len(df) > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def parse_macro_visa_csv(csv_path, output_path, file_type):
    """
    Parse Macro VISA CSV file (Autorizaciones or Movimientos) and generate Excel output
    """
    transactions = []

    # Read the CSV file with semicolon separator
    df = pd.read_csv(csv_path, sep=";")

    # Process each row
    for _, row in df.iterrows():
        # Handle different date column names between file types
        if file_type == "movs":
            fecha_str = (
                str(row["Fecha Origen"]).strip()
                if pd.notna(row["Fecha Origen"])
                else ""
            )
        else:
            fecha_str = str(row["Fecha"]).strip() if pd.notna(row["Fecha"]) else ""

        establecimiento = (
            str(row["Establecimiento"]).strip()
            if pd.notna(row["Establecimiento"])
            else ""
        )
        moneda = str(row["Moneda"]).strip() if pd.notna(row["Moneda"]) else ""
        importe_str = str(row["Importe"]).strip() if pd.notna(row["Importe"]) else ""

        if fecha_str and importe_str and importe_str != "nan":
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            try:
                day, month, year = fecha_str.split("/")
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                continue  # Skip invalid dates

            # Convert amount from European format to float
            try:
                # Handle European format: 10,500.00 -> 10500.00
                amount_str = importe_str.replace(",", "")
                amount = float(amount_str)
            except ValueError:
                continue  # Skip invalid amounts

            # Map currency
            currency = (
                "ARS" if moneda == "Pesos" else "USD" if moneda == "Dolares" else "ARS"
            )

            transaction = {
                "Date": formatted_date,
                "Description": establecimiento,
                "Currency": currency,
                "Amount": amount,
                "Payment Method": "Macro VISA",
            }
            transactions.append(transaction)

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output
    if len(df) > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def parse_mercadopago_xlsx(xlsx_path, output_path):
    """
    Parse Mercadopago XLSX file and generate Excel output
    """
    transactions = []

    # Read the XLSX file
    df = pd.read_excel(xlsx_path)

    # Process each row
    for _, row in df.iterrows():
        fecha_str = (
            str(row["Fecha de Pago"]).strip() if pd.notna(row["Fecha de Pago"]) else ""
        )
        tipo_operacion = (
            str(row["Tipo de Operación"]).strip()
            if pd.notna(row["Tipo de Operación"])
            else ""
        )
        importe = row["Importe"] if pd.notna(row["Importe"]) else 0

        if fecha_str and tipo_operacion:
            # Convert ISO 8601 timestamp to YYYY-MM-DD format
            try:
                # Extract date part from "2025-02-01T17:45:36Z"
                formatted_date = fecha_str.split("T")[0]
            except (ValueError, IndexError):
                continue  # Skip invalid dates

            # Amount is already in proper numeric format
            try:
                amount = float(importe)
            except (ValueError, TypeError):
                continue  # Skip invalid amounts

            transaction = {
                "Date": formatted_date,
                "Description": tipo_operacion,
                "Currency": "ARS",  # All Mercadopago transactions are in ARS
                "Amount": amount,
                "Payment Method": "Mercadopago",
            }
            transactions.append(transaction)

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Sort by date to match expected output (chronological order)
    if len(df) > 0:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    return df


def validate_csv_balance(input_csv_path, output_df, filename):
    """
    Validate CSV input totals against output Excel totals and log results
    """
    logger.info(f"[INFO] Validating CSV balance for: {filename}")

    # Read input CSV and calculate total
    input_df = pd.read_csv(input_csv_path, sep=";")
    input_total = 0
    for _, row in input_df.iterrows():
        importe_str = str(row["Importe"]).strip() if pd.notna(row["Importe"]) else ""
        if importe_str and importe_str != "nan":
            try:
                # Handle European format: remove commas
                amount_str = importe_str.replace(",", "")
                amount = float(amount_str)
                input_total += amount
            except ValueError:
                continue

    # Calculate output total
    output_total = output_df["Amount"].sum()

    # Calculate difference
    difference = input_total - output_total

    # Format numbers with thousand separators for logging
    input_formatted = f"{input_total:,.2f}"
    output_formatted = f"{output_total:,.2f}"

    logger.info(
        f"        Input CSV Total: {input_formatted} | "
        f"Output Excel Total: {output_formatted} | Δ: {difference:.2f}"
    )

    # Log warnings for mismatches (don't raise errors)
    if abs(difference) > 0.01:  # Allow for small rounding differences
        logger.warning(
            f"[WARNING] Total mismatch in {filename}: difference of {difference:.2f}"
        )

    return {"input": input_total, "output": output_total}


def validate_mercadopago_balance(input_xlsx_path, output_df, filename):
    """
    Validate Mercadopago XLSX input totals against output Excel totals and log results
    """
    logger.info(f"[INFO] Validating Mercadopago balance for: {filename}")

    # Read input XLSX and calculate total
    input_df = pd.read_excel(input_xlsx_path)
    input_total = 0
    for _, row in input_df.iterrows():
        importe = row["Importe"] if pd.notna(row["Importe"]) else 0
        try:
            amount = float(importe)
            input_total += amount
        except (ValueError, TypeError):
            continue

    # Calculate output total
    output_total = output_df["Amount"].sum()

    # Calculate difference
    difference = input_total - output_total

    # Format numbers with thousand separators for logging
    input_formatted = f"{input_total:,.2f}"
    output_formatted = f"{output_total:,.2f}"

    logger.info(
        f"        Input XLSX Total: {input_formatted} | "
        f"Output Excel Total: {output_formatted} | Δ: {difference:.2f}"
    )

    # Log warnings for mismatches (don't raise errors)
    if abs(difference) > 0.01:  # Allow for small rounding differences
        logger.warning(
            f"[WARNING] Total mismatch in {filename}: difference of {difference:.2f}"
        )

    return {"input": input_total, "output": output_total}


def convert_date(date_str):
    """Convert DD.MM.YY or DD-MMM-YY to YYYY-MM-DD format"""
    if "-" in date_str:
        # Handle DD-MMM-YY format (BBVA Mastercard)
        day, month_name, year = date_str.split("-")
        month_map = {
            "Jan": "01",
            "Ene": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "Abr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Ago": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
            "Dic": "12",
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
    print(f"\n{'=' * 60}")
    print(f"PROCESSING SUMMARY: {filename}")
    print(f"{'=' * 60}")
    print(f"Transactions Processed: {len(df)}")
    print(f"Output File: {output_path}")

    # Calculate totals including payments
    total_ars = df[df["Currency"] == "ARS"]["Amount"].sum()
    total_usd = df[df["Currency"] == "USD"]["Amount"].sum()

    print("\nACTUAL TOTALS (including payments):")
    print(f"  ARS: {total_ars:,.2f}")
    print(f"  USD: {total_usd:.2f}")

    print("\nBALANCE VALIDATION:")
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

    # Process BBVA Account statement
    print("Processing BBVA Account statement...")
    input_file = "input/BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls"
    output_file = "output/BBVA-Account-transactions.xlsx"
    df_bbva_account = parse_account_xls(input_file, output_file)

    # For XLS validation, compare against input file totals
    input_df = pd.read_excel(input_file)
    input_data_rows = input_df.iloc[2:]  # Skip header rows
    input_total = 0
    for _, row in input_data_rows.iterrows():
        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[3]):
            importe_str = str(row.iloc[3]).strip()
            if importe_str and importe_str != "nan":
                try:
                    amount_str = importe_str.replace(".", "").replace(",", ".")
                    amount = float(amount_str)
                    input_total += amount
                except ValueError:
                    continue

    computed_total = df_bbva_account["Amount"].sum()

    # Create balance objects for compatibility with existing summary function
    reported_bbva_account = {"ars": input_total, "usd": 0.0}
    computed_bbva_account = {"ars": computed_total, "usd": 0.0}

    results.append(
        (
            "BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls",
            df_bbva_account,
            reported_bbva_account,
            computed_bbva_account,
            output_file,
        )
    )

    # Process Macro Account statement
    print("Processing Macro Account statement...")
    input_file = "input/MACRO-movimientos-de-cuenta.xls"
    output_file = "output/Macro-Account-transactions.xlsx"
    df_macro_account = parse_macro_account_xls(input_file, output_file)

    # For Macro XLS validation, extract balance from first row of Saldo column
    input_df = pd.read_excel(input_file, header=None)
    first_saldo_value = input_df.iloc[3, 4]  # First data row, Saldo column

    # Parse "$ 34.122,00" format to 34122.00
    expected_total = float(first_saldo_value)

    computed_total = df_macro_account["Amount"].sum()

    # Create balance objects for compatibility with existing summary function
    reported_macro_account = {"ars": expected_total, "usd": 0.0}
    computed_macro_account = {"ars": computed_total, "usd": 0.0}

    results.append(
        (
            "MACRO-movimientos-de-cuenta.xls",
            df_macro_account,
            reported_macro_account,
            computed_macro_account,
            output_file,
        )
    )

    # Process BBVA VISA Autorizaciones CSV
    print("Processing BBVA VISA Autorizaciones CSV...")
    input_file = "input/BBVA-Visa-Autorizaciones.csv"
    output_file = "output/BBVA-Visa-auth-transactions.xlsx"
    df_bbva_auth = parse_bbva_visa_csv(input_file, output_file, "auth")

    # Validate CSV input vs output totals
    validation_result = validate_csv_balance(
        input_file, df_bbva_auth, "BBVA-Visa-Autorizaciones.csv"
    )

    # Create balance objects for compatibility with existing summary function
    reported_bbva_auth = {"ars": validation_result["input"], "usd": 0.0}
    computed_bbva_auth = {"ars": validation_result["output"], "usd": 0.0}

    results.append(
        (
            "BBVA-Visa-Autorizaciones.csv",
            df_bbva_auth,
            reported_bbva_auth,
            computed_bbva_auth,
            output_file,
        )
    )

    # Process BBVA VISA Movimientos CSV
    print("Processing BBVA VISA Movimientos CSV...")
    input_file = "input/BBVA-Visa-Movimientos.csv"
    output_file = "output/BBVA-Visa-movs-transactions.xlsx"
    df_bbva_movs = parse_bbva_visa_csv(input_file, output_file, "movs")

    # Validate CSV input vs output totals
    validation_result = validate_csv_balance(
        input_file, df_bbva_movs, "BBVA-Visa-Movimientos.csv"
    )

    # Create balance objects for compatibility with existing summary function
    reported_bbva_movs = {"ars": validation_result["input"], "usd": 0.0}
    computed_bbva_movs = {"ars": validation_result["output"], "usd": 0.0}

    results.append(
        (
            "BBVA-Visa-Movimientos.csv",
            df_bbva_movs,
            reported_bbva_movs,
            computed_bbva_movs,
            output_file,
        )
    )

    # Process MACRO VISA Autorizaciones CSV
    print("Processing MACRO VISA Autorizaciones CSV...")
    input_file = "input/MACRO-Visa-Autorizaciones.csv"
    output_file = "output/MACRO-Visa-auth-transactions.xlsx"
    df_macro_auth = parse_macro_visa_csv(input_file, output_file, "auth")

    # Validate CSV input vs output totals
    validation_result = validate_csv_balance(
        input_file, df_macro_auth, "MACRO-Visa-Autorizaciones.csv"
    )

    # Create balance objects for compatibility with existing summary function
    reported_macro_auth = {"ars": validation_result["input"], "usd": 0.0}
    computed_macro_auth = {"ars": validation_result["output"], "usd": 0.0}

    results.append(
        (
            "MACRO-Visa-Autorizaciones.csv",
            df_macro_auth,
            reported_macro_auth,
            computed_macro_auth,
            output_file,
        )
    )

    # Process MACRO VISA Movimientos CSV
    print("Processing MACRO VISA Movimientos CSV...")
    input_file = "input/MACRO-VISA-ult-Movimientos.csv"
    output_file = "output/MACRO-Visa-movs-transactions.xlsx"
    df_macro_movs = parse_macro_visa_csv(input_file, output_file, "movs")

    # Validate CSV input vs output totals
    validation_result = validate_csv_balance(
        input_file, df_macro_movs, "MACRO-VISA-ult-Movimientos.csv"
    )

    # Create balance objects for compatibility with existing summary function
    reported_macro_movs = {"ars": validation_result["input"], "usd": 0.0}
    computed_macro_movs = {"ars": validation_result["output"], "usd": 0.0}

    results.append(
        (
            "MACRO-VISA-ult-Movimientos.csv",
            df_macro_movs,
            reported_macro_movs,
            computed_macro_movs,
            output_file,
        )
    )

    # Process Mercadopago statement
    print("Processing Mercadopago statement...")
    input_file = "input/mercadopago.xlsx"
    output_file = "output/mercadopago-transactions.xlsx"
    df_mercadopago = parse_mercadopago_xlsx(input_file, output_file)

    # Validate Mercadopago input vs output totals
    validation_result = validate_mercadopago_balance(
        input_file, df_mercadopago, "mercadopago.xlsx"
    )

    # Create balance objects for compatibility with existing summary function
    reported_mercadopago = {"ars": validation_result["input"], "usd": 0.0}
    computed_mercadopago = {"ars": validation_result["output"], "usd": 0.0}

    results.append(
        (
            "mercadopago.xlsx",
            df_mercadopago,
            reported_mercadopago,
            computed_mercadopago,
            output_file,
        )
    )

    # Print organized summary for all files
    for filename, df, reported, computed, output_path in results:
        print_processing_summary(filename, df, reported, computed, output_path)

    print(f"\n{'=' * 60}")
    print("ALL PROCESSING COMPLETE")
    print(f"{'=' * 60}")
