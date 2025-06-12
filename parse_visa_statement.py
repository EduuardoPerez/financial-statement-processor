import pdfplumber
import pandas as pd
import re
import os


def detect_payment_method(full_text):
    """
    Detect payment method from PDF content
    Returns the payment method string (e.g., "Macro VISA", "BBVA VISA")
    """
    text_upper = full_text.upper()

    # Check for Macro bank indicators first (more specific)
    macro_indicators = ["MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR"]
    macro_found = any(indicator in text_upper for indicator in macro_indicators)

    # Check for BBVA bank indicators (more specific than just VISA SIGNATURE)
    bbva_indicators = ["BBVA", "WWW.BBVA.COM.AR"]
    bbva_found = any(indicator in text_upper for indicator in bbva_indicators)

    # Check for VISA indicators
    visa_found = "VISA" in text_upper

    if macro_found and visa_found:
        return "Macro VISA"
    elif bbva_found and visa_found:
        return "BBVA VISA"

    # Could add more bank/card combinations here in the future
    return "Unknown Payment Method"


def parse_visa_pdf(pdf_path, output_path):
    transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Detect payment method from PDF content
    payment_method = detect_payment_method(full_text)

    lines = full_text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Pattern for transaction lines with date
        date_pattern = r"(\d{2}\.\d{2}\.\d{2})\s+"
        match = re.match(date_pattern, line)

        if match:
            date_str = match.group(1)
            remaining_line = line[match.end() :].strip()

            # Skip certain lines but handle specific cases
            if "SALDO ANTERIOR" in remaining_line or "Total Consumos" in remaining_line:
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

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to Excel
    df.to_excel(output_path, index=False, sheet_name="Sheet1")

    print(f"Processed {len(transactions)} transactions")
    print(f"Total ARS amount: {df[df['Currency'] == 'ARS']['Amount'].sum():.2f}")
    print(f"Total USD amount: {df[df['Currency'] == 'USD']['Amount'].sum():.2f}")
    print(f"Saved to: {output_path}")

    return df


def convert_date(date_str):
    """Convert DD.MM.YY to YYYY-MM-DD format"""
    day, month, year = date_str.split(".")
    # Assuming 22 means 2022
    if int(year) < 50:
        full_year = 2000 + int(year)
    else:
        full_year = 1900 + int(year)

    return f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"


if __name__ == "__main__":
    # Example usage - processes both bank types automatically based on PDF content

    # Process Macro VISA statement
    print("=== Processing Macro VISA Statement ===")
    input_file = "input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"
    output_file = "output/MACRO-VISA-transactions.xlsx"
    df_macro = parse_visa_pdf(input_file, output_file)
    print(f"First 3 Macro transactions:")
    print(df_macro.head(3).to_string(index=False))

    print("\n=== Processing BBVA VISA Statement ===")
    # Process BBVA VISA statement
    input_file = "input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"
    output_file = "output/BBVA-VISA-transactions.xlsx"
    df_bbva = parse_visa_pdf(input_file, output_file)
    print(f"First 3 BBVA transactions:")
    print(df_bbva.head(3).to_string(index=False))
