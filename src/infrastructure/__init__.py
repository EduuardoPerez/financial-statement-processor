# Infrastructure layer - External adapters and implementations

from .config import ApplicationConfig, DatabaseConfig, OutputConfig, ProcessingConfig
from .detectors import BBVADetector, MacroDetector, build_default_payment_detector
from .factories import DefaultParserFactory
from .observers import ProgressTracker, ValidationReporter
from .parsers import PDFStatementParser, XLSStatementParser
from .repositories import ExcelStatementRepository

__all__ = [
    # Configuration
    "ApplicationConfig",
    "DatabaseConfig",
    "OutputConfig",
    "ProcessingConfig",
    # Detectors
    "MacroDetector",
    "BBVADetector",
    "build_default_payment_detector",
    # Factories
    "DefaultParserFactory",
    # Observers
    "ProgressTracker",
    "ValidationReporter",
    # Parsers
    "PDFStatementParser",
    "XLSStatementParser",
    # Repositories
    "ExcelStatementRepository",
]
