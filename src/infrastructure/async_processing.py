"""
Async/threaded batch processing for financial statements.

This module provides AsyncStatementProcessor for high-throughput batch processing
using both asyncio and concurrent.futures approaches. It integrates seamlessly
with the existing clean architecture and provides controlled concurrency,
error isolation, and progress tracking.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from application.services import ProcessingResult, StatementProcessingService
from domain.events import (
    EventPublisher,
    ProcessingCompletedEvent,
    ProcessingFailedEvent,
    ProcessingStartedEvent,
)
from domain.validation import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessingResult:
    """Result of batch processing operation with comprehensive metrics."""

    successful_files: list[Path] = field(default_factory=list)
    failed_files: list[tuple[Path, str]] = field(default_factory=list)
    total_processing_time: float = 0.0
    total_transactions: int = 0
    processing_mode: str = "unknown"

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total_files = len(self.successful_files) + len(self.failed_files)
        if total_files == 0:
            return 0.0
        return len(self.successful_files) / total_files

    @property
    def total_files(self) -> int:
        """Get total number of files processed."""
        return len(self.successful_files) + len(self.failed_files)

    def print_summary(self) -> None:
        """Print formatted summary of batch processing results."""
        print(f"\n{'=' * 60}")
        print("ASYNC BATCH PROCESSING SUMMARY")
        print(f"{'=' * 60}")
        print(f"🚀 Processing Mode: {self.processing_mode}")
        print(f"✅ Successful files: {len(self.successful_files)}")
        print(f"❌ Failed files: {len(self.failed_files)}")
        print(f"📊 Success rate: {self.success_rate:.1%}")
        print(f"📈 Total transactions: {self.total_transactions}")
        print(f"⏱️  Total processing time: {self.total_processing_time:.2f}s")

        if self.failed_files:
            print("\n❌ Failed Files:")
            for file_path, error in self.failed_files:
                print(f"   {file_path.name}: {error}")


class AsyncStatementProcessor:
    """
    Async/threaded batch processor for financial statements.

    Provides both asyncio and concurrent.futures-based processing modes
    with controlled concurrency, error isolation, and progress tracking.
    Integrates seamlessly with existing clean architecture components.
    """

    def __init__(
        self,
        processing_service: StatementProcessingService,
        max_workers: int = 4,
        use_asyncio: bool = True,
        event_publisher: EventPublisher | None = None,
    ):
        """
        Initialize AsyncStatementProcessor.

        Args:
            processing_service: Service for processing individual statements
            max_workers: Maximum number of concurrent workers
            use_asyncio: Whether to use asyncio (True) or ThreadPoolExecutor (False)
            event_publisher: Optional event publisher for progress tracking
        """
        self._processing_service = processing_service
        self._max_workers = max_workers
        self._use_asyncio = use_asyncio
        self._event_publisher = event_publisher

        # Initialize ThreadPoolExecutor for non-asyncio mode
        self._executor: ThreadPoolExecutor | None = None
        if not use_asyncio:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch_async(
        self, file_paths: list[Path], output_dir: Path
    ) -> AsyncIterator[ProcessingResult]:
        """
        Process multiple files using asyncio with controlled concurrency.

        Args:
            file_paths: List of input file paths to process
            output_dir: Directory for output files

        Yields:
            ProcessingResult: Individual file processing results as they complete

        Example:
            >>> processor = AsyncStatementProcessor(service, max_workers=2)
            >>> files = [Path("file1.pdf"), Path("file2.xls")]
            >>> async for result in processor.process_batch_async(files, Path("output")):
            ...     print(f"Processed: {result.input_path.name}")
        """
        if not self._use_asyncio:
            raise ValueError(
                "AsyncStatementProcessor configured for threading mode, not asyncio"
            )

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self._max_workers)

        async def process_single_file(file_path: Path) -> ProcessingResult:
            """Process a single file with semaphore control."""
            async with semaphore:
                # Publish processing started event
                if self._event_publisher:
                    try:
                        file_size = (
                            file_path.stat().st_size if file_path.exists() else 0
                        )
                        event = ProcessingStartedEvent(
                            file_path=file_path, file_size=file_size
                        )
                        self._event_publisher.publish(event)
                    except Exception as e:
                        logger.warning(
                            f"Failed to publish processing started event: {e}"
                        )

                # Run synchronous processing in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                try:
                    result = await loop.run_in_executor(
                        None,  # Use default thread pool
                        self._process_file_sync,
                        file_path,
                        output_dir,
                    )

                    # Publish completion event
                    if self._event_publisher and result.success and result.output_path:
                        try:
                            completed_event = ProcessingCompletedEvent(
                                file_path=file_path,
                                output_path=result.output_path,
                                transaction_count=(
                                    len(result.statement.transactions)
                                    if result.statement
                                    else 0
                                ),
                                processing_time=result.processing_time,
                            )
                            self._event_publisher.publish(completed_event)
                        except Exception as e:
                            logger.warning(
                                f"Failed to publish processing completed event: {e}"
                            )

                    return result

                except Exception as e:
                    # Create failed result for exceptions
                    error_msg = f"Processing failed: {str(e)}"

                    # Publish failure event
                    if self._event_publisher:
                        try:
                            failed_event = ProcessingFailedEvent(
                                file_path=file_path,
                                error_message=error_msg,
                                exception_type=type(e).__name__,
                            )
                            self._event_publisher.publish(failed_event)
                        except Exception as pub_error:
                            logger.warning(
                                f"Failed to publish processing failed event: {pub_error}"
                            )

                    # Create error validation result
                    error_validation = ValidationResult(
                        is_valid=False, errors=[error_msg]
                    )

                    return ProcessingResult(
                        input_path=file_path,
                        output_path=None,
                        statement=None,
                        validation_result=error_validation,
                        success=False,
                        errors=[error_msg],
                        processing_time=0.0,
                    )

        # Create tasks for all files
        tasks = [process_single_file(file_path) for file_path in file_paths]

        # Yield results as they complete
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                yield result
            except Exception as e:
                logger.error(f"Unexpected error in async processing: {e}")
                # Create error result for unexpected failures
                error_validation = ValidationResult(
                    is_valid=False, errors=[f"Unexpected error: {str(e)}"]
                )
                yield ProcessingResult(
                    input_path=Path("unknown"),
                    output_path=None,
                    statement=None,
                    validation_result=error_validation,
                    success=False,
                    errors=[f"Unexpected error: {str(e)}"],
                    processing_time=0.0,
                )

    def process_batch_threaded(
        self, file_paths: list[Path], output_dir: Path
    ) -> Iterator[ProcessingResult]:
        """
        Process multiple files using ThreadPoolExecutor.

        Args:
            file_paths: List of input file paths to process
            output_dir: Directory for output files

        Yields:
            ProcessingResult: Individual file processing results as they complete

        Example:
            >>> processor = AsyncStatementProcessor(service, use_asyncio=False)
            >>> files = [Path("file1.pdf"), Path("file2.xls")]
            >>> for result in processor.process_batch_threaded(files, Path("output")):
            ...     print(f"Processed: {result.input_path.name}")
        """
        if self._use_asyncio:
            raise ValueError(
                "AsyncStatementProcessor configured for asyncio mode, not threading"
            )

        if self._executor is None:
            raise RuntimeError("ThreadPoolExecutor not initialized")

        # Submit all files for processing
        future_to_path = {
            self._executor.submit(
                self._process_file_sync, file_path, output_dir
            ): file_path
            for file_path in file_paths
        }

        # Yield results as they complete
        for future in as_completed(future_to_path):
            file_path = future_to_path[future]

            try:
                result = future.result()

                # Publish events if event publisher is available
                if self._event_publisher:
                    try:
                        if result.success and result.output_path:
                            completed_event = ProcessingCompletedEvent(
                                file_path=file_path,
                                output_path=result.output_path,
                                transaction_count=(
                                    len(result.statement.transactions)
                                    if result.statement
                                    else 0
                                ),
                                processing_time=result.processing_time,
                            )
                            self._event_publisher.publish(completed_event)
                        else:
                            failed_event = ProcessingFailedEvent(
                                file_path=file_path,
                                error_message="; ".join(result.errors),
                                exception_type="ProcessingError",
                            )
                            self._event_publisher.publish(failed_event)
                    except Exception as e:
                        logger.warning(f"Failed to publish event: {e}")

                yield result

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

                # Publish failure event
                if self._event_publisher:
                    try:
                        failure_event = ProcessingFailedEvent(
                            file_path=file_path,
                            error_message=f"Processing failed: {str(e)}",
                            exception_type=type(e).__name__,
                        )
                        self._event_publisher.publish(failure_event)
                    except Exception as pub_error:
                        logger.warning(f"Failed to publish failure event: {pub_error}")

                # Create error result
                error_validation = ValidationResult(
                    is_valid=False, errors=[f"Processing failed: {str(e)}"]
                )
                yield ProcessingResult(
                    input_path=file_path,
                    output_path=None,
                    statement=None,
                    validation_result=error_validation,
                    success=False,
                    errors=[f"Processing failed: {str(e)}"],
                    processing_time=0.0,
                )

    async def process_batch_complete(
        self, file_paths: list[Path], output_dir: Path
    ) -> BatchProcessingResult:
        """
        Process batch of files and return complete results.

        Args:
            file_paths: List of input file paths to process
            output_dir: Directory for output files

        Returns:
            BatchProcessingResult: Comprehensive batch processing results

        Example:
            >>> processor = AsyncStatementProcessor(service)
            >>> files = [Path("file1.pdf"), Path("file2.xls")]
            >>> result = await processor.process_batch_complete(files, Path("output"))
            >>> result.print_summary()
        """
        start_time = time.time()
        batch_result = BatchProcessingResult(
            processing_mode="asyncio" if self._use_asyncio else "threading"
        )

        try:
            if self._use_asyncio:
                # Use asyncio processing
                async for result in self.process_batch_async(file_paths, output_dir):
                    if result.success:
                        batch_result.successful_files.append(result.input_path)
                        if result.statement:
                            batch_result.total_transactions += len(
                                result.statement.transactions
                            )
                    else:
                        error_msg = (
                            "; ".join(result.errors)
                            if result.errors
                            else "Unknown error"
                        )
                        batch_result.failed_files.append((result.input_path, error_msg))
            else:
                # Use threading processing
                for result in self.process_batch_threaded(file_paths, output_dir):
                    if result.success:
                        batch_result.successful_files.append(result.input_path)
                        if result.statement:
                            batch_result.total_transactions += len(
                                result.statement.transactions
                            )
                    else:
                        error_msg = (
                            "; ".join(result.errors)
                            if result.errors
                            else "Unknown error"
                        )
                        batch_result.failed_files.append((result.input_path, error_msg))

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Add all files as failed if batch processing itself fails
            for file_path in file_paths:
                if file_path not in [f[0] for f in batch_result.failed_files]:
                    batch_result.failed_files.append(
                        (file_path, f"Batch processing error: {str(e)}")
                    )

        batch_result.total_processing_time = time.time() - start_time
        return batch_result

    def _process_file_sync(self, file_path: Path, output_dir: Path) -> ProcessingResult:
        """
        Synchronous file processing for use in thread pools.

        Args:
            file_path: Input file path
            output_dir: Output directory

        Returns:
            ProcessingResult: Processing result with success/failure details
        """
        try:
            return self._processing_service.process_statement(file_path, output_dir)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            error_validation = ValidationResult(
                is_valid=False, errors=[f"Processing failed: {str(e)}"]
            )
            return ProcessingResult(
                input_path=file_path,
                output_path=None,
                statement=None,
                validation_result=error_validation,
                success=False,
                errors=[f"Processing failed: {str(e)}"],
                processing_time=0.0,
            )

    def close(self) -> None:
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        self.close()


# Convenience function for quick batch processing
async def process_files_async(
    file_paths: list[Path],
    output_dir: Path,
    processing_service: StatementProcessingService,
    max_workers: int = 4,
    use_asyncio: bool = True,
    event_publisher: EventPublisher | None = None,
) -> BatchProcessingResult:
    """
    Convenience function for async batch processing.

    Args:
        file_paths: List of input file paths
        output_dir: Output directory
        processing_service: Statement processing service
        max_workers: Maximum concurrent workers
        use_asyncio: Whether to use asyncio or threading
        event_publisher: Optional event publisher

    Returns:
        BatchProcessingResult: Complete batch processing results

    Example:
        >>> files = [Path("file1.pdf"), Path("file2.xls")]
        >>> result = await process_files_async(files, Path("output"), service)
        >>> print(f"Success rate: {result.success_rate:.1%}")
    """
    async with AsyncStatementProcessor(
        processing_service=processing_service,
        max_workers=max_workers,
        use_asyncio=use_asyncio,
        event_publisher=event_publisher,
    ) as processor:
        result: BatchProcessingResult = await processor.process_batch_complete(
            file_paths, output_dir
        )
        return result
