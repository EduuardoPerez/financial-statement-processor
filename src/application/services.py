"""
Application services for the Financial Statement Processor.

This module contains the application layer services that orchestrate
domain and infrastructure components to fulfill business use cases.
Following clean architecture principles, these services coordinate
without containing business logic themselves.

Classes:
    ProcessingResult: Result of statement processing
    StatementProcessingService: Main orchestrator service
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from domain.factories import ParserFactory
from domain.filename import FilenameGenerator
from domain.models import ConsolidatedStatement, Statement, Transaction
from domain.repositories import StatementRepository
from domain.services import DuplicateDetector
from domain.validation import StatementValidator, ValidationResult
from infrastructure.config import ProcessingConfig
from infrastructure.extractors import BalanceExtractionService


@dataclass
class ProcessingResult:
    """
    Result of statement processing operation.

    Attributes:
        input_path: Path to the input file that was processed
        output_path: Path to the generated output file (None if failed)
        statement: Parsed statement object (None if parsing failed)
        validation_result: Result of statement validation
        success: Whether the processing completed successfully
        errors: List of error messages encountered during processing
        processing_time: Time taken to process the statement in seconds
    """

    input_path: Path
    output_path: Path | None
    statement: Statement | None
    validation_result: ValidationResult
    success: bool
    errors: list[str] = field(default_factory=list)
    processing_time: float = 0.0


@dataclass
class ConsolidationResult:
    """
    Result of consolidation operation.

    Attributes:
        input_directory: Directory containing input statement files
        output_path: Path to the generated consolidated file (None if failed)
        consolidated_statement: Consolidated statement object (None if failed)
        successful_files: List of successfully processed files with details
        failed_files: List of failed files with comprehensive error information
        total_transactions: Total number of transactions in consolidation
        duplicate_count: Number of duplicate transactions found and marked
        processing_time: Time taken to complete consolidation in seconds
        success: Whether the consolidation completed successfully
        errors: List of general error messages encountered during consolidation
    """

    input_directory: Path
    output_path: Path | None
    consolidated_statement: ConsolidatedStatement | None
    successful_files: list[dict[str, Any]] = field(default_factory=list)
    failed_files: list[dict[str, Any]] = field(default_factory=list)
    total_transactions: int = 0
    duplicate_count: int = 0
    processing_time: float = 0.0
    success: bool = False
    errors: list[str] = field(default_factory=list)


class StatementProcessingService:
    """
    Main orchestrator service for statement processing.

    This service coordinates the parsing, validation, and persistence
    of financial statements. It follows the Single Responsibility
    Principle by orchestrating other components without containing
    business logic itself.

    The service implements a clean workflow:
    1. Create appropriate parser using factory
    2. Parse the input file into a Statement
    3. Validate the parsed statement
    4. Generate output filename
    5. Save statement via repository
    6. Return comprehensive processing result
    """

    def __init__(
        self,
        parser_factory: ParserFactory,
        repository: StatementRepository,
        validator: StatementValidator,
        filename_generator: FilenameGenerator,
        processing_config: ProcessingConfig,
        balance_extraction_service: BalanceExtractionService | None = None,
    ):
        """
        Initialize the processing service.

        Args:
            parser_factory: Factory for creating statement parsers
            repository: Repository for saving statements
            validator: Validator for statement validation
            filename_generator: Generator for output filenames
            processing_config: Configuration for processing behavior
            balance_extraction_service: Optional service for balance extraction
        """
        self._parser_factory = parser_factory
        self._repository = repository
        self._validator = validator
        self._filename_generator = filename_generator
        self._processing_config = processing_config
        self._balance_extraction_service = balance_extraction_service

    def process_statement(self, input_path: Path, output_dir: Path) -> ProcessingResult:
        """
        Process a statement file end-to-end.

        This method orchestrates the complete statement processing workflow:
        parsing, validation, filename generation, and persistence.

        Args:
            input_path: Path to the input statement file
            output_dir: Directory where output file should be saved

        Returns:
            ProcessingResult with details of the processing operation
        """
        start_time = time.time()
        errors: list[str] = []
        statement: Statement | None = None
        output_path: Path | None = None
        validation_result = ValidationResult(
            is_valid=False, errors=["Processing not completed"]
        )

        try:
            # Step 1: Create appropriate parser
            try:
                parser = self._parser_factory.create_parser(input_path)
            except ValueError as e:
                errors.append(f"No parser available: {str(e)}")
                return self._create_error_result(
                    input_path,
                    start_time,
                    errors,
                    statement,
                    output_path,
                    validation_result,
                )

            # Step 2: Parse the statement (with enhanced validation if available)
            try:
                # Try enhanced parsing with content if parser supports it
                if hasattr(parser, "parse_with_content") and hasattr(
                    self._validator, "validate_with_content"
                ):
                    statement, raw_content = parser.parse_with_content(input_path)

                    # Step 3: Enhanced validation with content
                    validation_result = self._validator.validate_with_content(
                        statement, raw_content
                    )
                else:
                    # Fall back to regular parsing
                    statement = parser.parse(input_path)

                    # Step 3: Regular validation
                    validation_result = self._validator.validate(statement)

                if not validation_result.is_valid:
                    errors.extend(validation_result.errors)
                    return self._create_error_result(
                        input_path,
                        start_time,
                        errors,
                        statement,
                        output_path,
                        validation_result,
                    )
            except Exception as e:
                errors.append(f"Parsing/validation failed: {str(e)}")
                val_result = ValidationResult(is_valid=False, errors=[str(e)])
                validation_result = val_result
                return self._create_error_result(
                    input_path,
                    start_time,
                    errors,
                    statement,
                    output_path,
                    validation_result,
                )

            # Step 4: Generate output filename
            try:
                output_filename = self._filename_generator.generate(statement)
                output_path = output_dir / output_filename
            except Exception as e:
                errors.append(f"Filename generation failed: {str(e)}")
                return self._create_error_result(
                    input_path,
                    start_time,
                    errors,
                    statement,
                    output_path,
                    validation_result,
                )

            # Step 5: Save statement via repository
            try:
                self._repository.save_statement(statement, output_path)
            except Exception as e:
                errors.append(f"Save failed: {str(e)}")
                return self._create_error_result(
                    input_path,
                    start_time,
                    errors,
                    statement,
                    output_path,
                    validation_result,
                )

            # Step 6: Return successful result
            processing_time = time.time() - start_time
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                statement=statement,
                validation_result=validation_result,
                success=True,
                errors=[],
                processing_time=processing_time,
            )

        except Exception as e:
            # Catch any unexpected exceptions
            errors.append(f"Unexpected error: {str(e)}")
            return self._create_error_result(
                input_path,
                start_time,
                errors,
                statement,
                output_path,
                validation_result,
            )

    def _create_error_result(
        self,
        input_path: Path,
        start_time: float,
        errors: list[str],
        statement: Statement | None,
        output_path: Path | None,
        validation_result: ValidationResult,
    ) -> ProcessingResult:
        """
        Create a ProcessingResult for error cases.

        Args:
            input_path: Path to the input file
            start_time: Processing start time
            errors: List of error messages
            statement: Parsed statement (may be None)
            output_path: Output path (may be None)
            validation_result: Validation result

        Returns:
            ProcessingResult indicating failure
        """
        processing_time = time.time() - start_time
        return ProcessingResult(
            input_path=input_path,
            output_path=output_path,
            statement=statement,
            validation_result=validation_result,
            success=False,
            errors=errors,
            processing_time=processing_time,
        )

    def consolidate_statements(
        self, input_dir: Path, output_dir: Path
    ) -> ConsolidationResult:
        """
        Consolidate multiple statement files into single output.

        Workflow:
        1. Discover all supported files in input directory
        2. Parse and validate each file individually
        3. Collect all transactions from successful parses
        4. Sort transactions chronologically (oldest to newest)
        5. Detect and mark duplicates
        6. Create consolidated statement
        7. Generate consolidated filename
        8. Save consolidated Excel file

        Args:
            input_dir: Directory containing statement files
            output_dir: Directory for consolidated output

        Returns:
            ConsolidationResult with processing details
        """
        start_time = time.time()

        # Discover supported files
        files = self._discover_statement_files(input_dir)

        if not files:
            return ConsolidationResult(
                input_directory=input_dir,
                output_path=None,
                consolidated_statement=None,
                success=False,
                processing_time=time.time() - start_time,
                errors=["No supported files found in directory"],
            )

        # Process each file individually
        successful_statements: list[Statement] = []
        successful_files: list[dict[str, Any]] = []
        failed_files: list[dict[str, Any]] = []

        for file_path in files:
            statement, errors = self._process_individual_file(file_path)
            if statement:
                successful_statements.append(statement)
                successful_files.append(
                    {
                        "file": str(file_path),
                        "transactions": len(statement.transactions),
                        "payment_method": statement.payment_method.value,
                    }
                )
            else:
                failed_files.append(
                    {
                        "file": str(file_path),
                        "errors": errors,
                    }
                )

        # Check if we have any successful statements
        if not successful_statements:
            return ConsolidationResult(
                input_directory=input_dir,
                output_path=None,
                consolidated_statement=None,
                successful_files=successful_files,
                failed_files=failed_files,
                success=False,
                processing_time=time.time() - start_time,
                errors=["No valid statements could be processed"],
            )

        # Collect and sort all transactions
        all_transactions = self._collect_all_transactions(successful_statements)
        sorted_transactions = self._sort_transactions_chronologically(all_transactions)

        # Detect and mark duplicates with configured prefix
        detector = DuplicateDetector(self._processing_config.duplicate_prefix)
        processed_transactions, duplicate_count = detector.mark_duplicates(
            sorted_transactions
        )

        # Create consolidated statement
        consolidated = ConsolidatedStatement(
            transactions=processed_transactions,
            source_statements=successful_statements,
            duplicate_count=duplicate_count,
        )

        # Add source statements to consolidated
        for statement in successful_statements:
            consolidated.add_statement(statement)

        # Generate consolidated filename and save
        try:
            filename = self._filename_generator.generate_consolidated(
                processed_transactions
            )
            output_path = output_dir / filename

            # Save consolidated statement (need to enhance repository)
            if hasattr(self._repository, "save_consolidated_statement"):
                self._repository.save_consolidated_statement(consolidated, output_path)
            else:
                # Fallback: create a regular statement for now
                dummy_statement = Statement(
                    payment_method=(
                        processed_transactions[0].payment_method
                        if processed_transactions
                        else successful_statements[0].payment_method
                    ),
                    transactions=processed_transactions,
                )
                self._repository.save_statement(dummy_statement, output_path)

            return ConsolidationResult(
                input_directory=input_dir,
                output_path=output_path,
                consolidated_statement=consolidated,
                successful_files=successful_files,
                failed_files=failed_files,
                total_transactions=len(processed_transactions),
                duplicate_count=duplicate_count,
                processing_time=time.time() - start_time,
                success=True,
            )

        except Exception as e:
            return ConsolidationResult(
                input_directory=input_dir,
                output_path=None,
                consolidated_statement=consolidated,
                successful_files=successful_files,
                failed_files=failed_files,
                total_transactions=len(processed_transactions),
                duplicate_count=duplicate_count,
                processing_time=time.time() - start_time,
                success=False,
                errors=[f"Failed to save consolidated file: {str(e)}"],
            )

    def _discover_statement_files(self, input_dir: Path) -> list[Path]:
        """Find all supported statement files in directory."""
        supported_extensions = self._parser_factory.get_supported_extensions()
        files: list[Path] = []
        for ext in supported_extensions:
            files.extend(input_dir.glob(f"*{ext}"))
            files.extend(input_dir.glob(f"*{ext.upper()}"))
        return sorted(set(files))  # Remove duplicates and sort

    def _process_individual_file(
        self, file_path: Path
    ) -> tuple[Statement | None, list[str]]:
        """Process single file and return statement or errors."""
        try:
            result = self.process_statement(file_path, Path("temp"))
            if result.success and result.statement:
                return result.statement, []
            else:
                return None, result.errors
        except Exception as e:
            return None, [str(e)]

    def _collect_all_transactions(
        self, statements: list[Statement]
    ) -> list[Transaction]:
        """Collect and sort all transactions chronologically."""
        all_transactions: list[Transaction] = []
        for statement in statements:
            all_transactions.extend(statement.transactions)
        return all_transactions

    def _sort_transactions_chronologically(
        self, transactions: list[Transaction]
    ) -> list[Transaction]:
        """Sort transactions by date ascending (oldest first)."""
        return sorted(transactions, key=lambda t: t.date)
