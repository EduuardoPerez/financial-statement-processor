"""Shared helpers for infrastructure parsers."""

from domain.models import Currency


def parse_ddmmyyyy(date_str: str) -> str:
    """Convert DD/MM/YYYY to YYYY-MM-DD (ISO)."""
    day, month, year = date_str.split("/")
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def map_currency_es(moneda: str) -> Currency:
    """Map the Spanish currency name used by Argentine banks to the Currency enum."""
    return Currency.USD if moneda == "Dolares" else Currency.ARS
