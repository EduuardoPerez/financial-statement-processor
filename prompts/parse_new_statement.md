# 🛠️ Task: Extend `@parse_visa_statement.py` to Support BBVA Visa Statements

## 🎯 Objective

Update the existing `@parse_visa_statement.py` script so it can **also parse BBVA Visa PDF account summaries** and generate a valid `.xlsx` output file.

---

## ✅ Current Behavior

The script currently parses @input/MACRO-VISA-visa_account_summary_Dec_2022.pdf into @output/MACRO-VISA-transactions.xlsx

This functionality **must remain intact and unmodified**.

---

## ➕ New Requirement

Add support to parse the @input/BBVA-Visa-visa_account_summary_Apr_2025.pdf file and convert it into @output/BBVA-VISA-transactions.xlsx

The generated output must **match the structure** of this reference file @expected_output/BBVA-VISA-transactions.xlsx which is basically the same structure as @output/MACRO-VISA-transactions.xlsx but with the data specific to BBVA Visa transactions.

---

## 🧪 Validation Criteria

- The number of rows in the output file must match the number of rows in `@expected_output/BBVA-VISA-transactions.xlsx`.
- The total sum of the `Amount` column in the output must exactly match the expected output file.
- The structure (columns, formatting, etc.) must be the same.
- **All current functionality for MACRO Visa files must continue to work as-is.**
