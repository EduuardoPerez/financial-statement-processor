"""Shared helpers for infrastructure parsers."""

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pandas as pd

from domain.models import Currency, ExtractionResult, SourceProvenance, Transaction


def extraction_for_file(path: Path) -> ExtractionResult:
    return ExtractionResult(hashlib.sha256(path.read_bytes()).hexdigest())


def verify_file_unchanged(path: Path, report: ExtractionResult) -> None:
    if extraction_for_file(path).file_sha256 != report.file_sha256:
        raise OSError(f"Input file changed during extraction: {path}")


def source_text(value: object) -> str:
    return str(value) if pd.notna(cast(Any, value)) else ""


def is_blank_row(row: pd.Series) -> bool:
    return all(not source_text(value).strip() for value in row)


def retain_transaction(
    transaction: Transaction,
    report: ExtractionResult | None,
    locator: str,
    raw_date: str,
    raw_amount: str,
    raw_description: str,
    *,
    raw_currency: str | None = None,
    raw_dates: dict[str, str] | None = None,
    native_ids: dict[str, str] | None = None,
    references: dict[str, str] | None = None,
) -> Transaction:
    if report is None:
        return transaction
    report.retain()
    return replace(
        transaction,
        provenance=SourceProvenance(
            file_sha256=report.file_sha256,
            locator=locator,
            raw_date=raw_date,
            raw_amount=raw_amount,
            raw_description=raw_description,
            raw_currency=raw_currency,
            raw_dates=raw_dates or {},
            native_ids=native_ids or {},
            references=references or {},
        ),
    )


def parse_ddmmyyyy(date_str: str) -> str:
    """Convert DD/MM/YYYY to YYYY-MM-DD (ISO)."""
    day, month, year = date_str.split("/")
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def map_currency_spanish(currency_name: str) -> Currency:
    """Map the Spanish currency name used by Argentine banks to the Currency enum."""
    return Currency.USD if currency_name == "Dolares" else Currency.ARS
