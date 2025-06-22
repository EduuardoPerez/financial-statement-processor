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

from domain.factories import ParserFactory
from domain.filename import FilenameGenerator
from domain.models import Statement
from domain.repositories import StatementRepository
from domain.validation import StatementValidator, ValidationResult

__all__ = [
    "ProcessingResult",
    "StatementProcessingService",
]


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
    ):
        """
        Initialize the processing service.

        Args:
            parser_factory: Factory for creating statement parsers
            repository: Repository for saving statements
            validator: Validator for statement validation
            filename_generator: Generator for output filenames
        """
        self._parser_factory = parser_factory
        self._repository = repository
        self._validator = validator
        self._filename_generator = filename_generator

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

            # Step 2: Parse the statement
            try:
                statement = parser.parse(input_path)
            except Exception as e:
                errors.append(f"Parsing failed: {str(e)}")
                return self._create_error_result(
                    input_path,
                    start_time,
                    errors,
                    statement,
                    output_path,
                    validation_result,
                )

            # Step 3: Validate the statement
            try:
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
                errors.append(f"Validation failed: {str(e)}")
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
