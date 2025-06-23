"""
Unit tests for AsyncStatementProcessor.

Tests the async/threaded batch processing functionality including
asyncio and threading modes, error handling, and event integration.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from application.services import ProcessingResult
from domain.events import (
    EventPublisher,
)
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.validation import ValidationResult
from infrastructure.async_processing import (
    AsyncStatementProcessor,
    BatchProcessingResult,
    process_files_async,
)


class TestBatchProcessingResult:
    """Test BatchProcessingResult data class."""

    def test_success_rate_calculation(self):
        """Test success rate calculation with various scenarios."""
        result = BatchProcessingResult()

        # Empty result
        assert result.success_rate == 0.0

        # All successful
        result.successful_files = [Path("file1.pdf"), Path("file2.pdf")]
        assert result.success_rate == 1.0

        # Mixed results
        result.failed_files = [
            (Path("file3.pdf"), "error"),
            (Path("file4.pdf"), "error"),
        ]
        assert result.success_rate == 0.5

    def test_total_files_property(self):
        """Test total files calculation."""
        result = BatchProcessingResult()
        result.successful_files = [Path("file1.pdf")]
        result.failed_files = [(Path("file2.pdf"), "error")]

        assert result.total_files == 2

    def test_print_summary(self, capsys):
        """Test summary printing."""
        result = BatchProcessingResult(
            successful_files=[Path("success.pdf")],
            failed_files=[(Path("failed.pdf"), "Test error")],
            total_processing_time=1.5,
            total_transactions=100,
            processing_mode="asyncio",
        )

        result.print_summary()
        captured = capsys.readouterr()

        assert "ASYNC BATCH PROCESSING SUMMARY" in captured.out
        assert "Processing Mode: asyncio" in captured.out
        assert "Successful files: 1" in captured.out
        assert "Failed files: 1" in captured.out
        assert "Success rate: 50.0%" in captured.out
        assert "Total transactions: 100" in captured.out
        assert "Total processing time: 1.50s" in captured.out
        assert "failed.pdf: Test error" in captured.out


class TestAsyncStatementProcessor:
    """Test AsyncStatementProcessor class."""

    @pytest.fixture
    def mock_processing_service(self):
        """Create mock processing service."""
        service = Mock()

        # Create successful processing result
        from datetime import date
        from decimal import Decimal

        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            transactions=[
                Transaction(
                    date=date(2025, 1, 1),
                    description="Test transaction",
                    amount=Decimal("100.0"),
                    currency=Currency.ARS,
                    payment_method=PaymentMethod.BBVA_VISA,
                )
            ],
        )

        validation_result = ValidationResult(is_valid=True, errors=[])

        success_result = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            statement=statement,
            validation_result=validation_result,
            success=True,
            errors=[],
            processing_time=0.5,
        )

        service.process_statement.return_value = success_result
        return service

    @pytest.fixture
    def mock_event_publisher(self):
        """Create mock event publisher."""
        return Mock(spec=EventPublisher)

    def test_init_asyncio_mode(self, mock_processing_service):
        """Test initialization in asyncio mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=2, use_asyncio=True
        )

        assert processor._processing_service == mock_processing_service
        assert processor._max_workers == 2
        assert processor._use_asyncio is True
        assert processor._executor is None

    def test_init_threading_mode(self, mock_processing_service):
        """Test initialization in threading mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=3, use_asyncio=False
        )

        assert processor._processing_service == mock_processing_service
        assert processor._max_workers == 3
        assert processor._use_asyncio is False
        assert isinstance(processor._executor, ThreadPoolExecutor)

        # Clean up
        processor.close()

    @pytest.mark.asyncio
    async def test_process_batch_async_success(self, mock_processing_service):
        """Test successful async batch processing."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=2, use_asyncio=True
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        results = []
        async for result in processor.process_batch_async(files, output_dir):
            results.append(result)

        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_processing_service.process_statement.call_count == 2

    @pytest.mark.asyncio
    async def test_process_batch_async_with_events(
        self, mock_processing_service, mock_event_publisher
    ):
        """Test async processing with event publishing."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service,
            max_workers=1,
            use_asyncio=True,
            event_publisher=mock_event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = []
        async for result in processor.process_batch_async(files, output_dir):
            results.append(result)

        assert len(results) == 1
        assert results[0].success

        # Verify events were published
        assert mock_event_publisher.publish.call_count >= 2  # Started + Completed

    @pytest.mark.asyncio
    async def test_process_batch_async_wrong_mode(self, mock_processing_service):
        """Test async processing when configured for threading mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=False
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        with pytest.raises(ValueError, match="configured for threading mode"):
            async for _ in processor.process_batch_async(files, output_dir):
                pass

        processor.close()

    def test_process_batch_threaded_success(self, mock_processing_service):
        """Test successful threaded batch processing."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=2, use_asyncio=False
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        results = list(processor.process_batch_threaded(files, output_dir))

        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_processing_service.process_statement.call_count == 2

        processor.close()

    def test_process_batch_threaded_wrong_mode(self, mock_processing_service):
        """Test threaded processing when configured for asyncio mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=True
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        with pytest.raises(ValueError, match="configured for asyncio mode"):
            list(processor.process_batch_threaded(files, output_dir))

    def test_process_batch_threaded_no_executor(self, mock_processing_service):
        """Test threaded processing without executor initialized."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=False
        )

        # Manually set executor to None to simulate error condition
        processor._executor = None

        files = [Path("test.pdf")]
        output_dir = Path("output")

        with pytest.raises(RuntimeError, match="ThreadPoolExecutor not initialized"):
            list(processor.process_batch_threaded(files, output_dir))

    @pytest.mark.asyncio
    async def test_process_batch_complete_asyncio(self, mock_processing_service):
        """Test complete batch processing in asyncio mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=2, use_asyncio=True
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        result = await processor.process_batch_complete(files, output_dir)

        assert isinstance(result, BatchProcessingResult)
        assert result.processing_mode == "asyncio"
        assert len(result.successful_files) == 2
        assert len(result.failed_files) == 0
        assert result.success_rate == 1.0
        assert result.total_transactions == 2  # 1 transaction per file

    @pytest.mark.asyncio
    async def test_process_batch_complete_threading(self, mock_processing_service):
        """Test complete batch processing in threading mode."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, max_workers=2, use_asyncio=False
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        result = await processor.process_batch_complete(files, output_dir)

        assert isinstance(result, BatchProcessingResult)
        assert result.processing_mode == "threading"
        assert len(result.successful_files) == 2
        assert len(result.failed_files) == 0

        processor.close()

    def test_process_file_sync_success(self, mock_processing_service):
        """Test synchronous file processing."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=True
        )

        file_path = Path("test.pdf")
        output_dir = Path("output")

        result = processor._process_file_sync(file_path, output_dir)

        assert result.success
        assert result.input_path == file_path
        mock_processing_service.process_statement.assert_called_once_with(
            file_path, output_dir
        )

    def test_process_file_sync_error(self, mock_processing_service):
        """Test synchronous file processing with error."""
        mock_processing_service.process_statement.side_effect = Exception("Test error")

        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=True
        )

        file_path = Path("test.pdf")
        output_dir = Path("output")

        result = processor._process_file_sync(file_path, output_dir)

        assert not result.success
        assert result.input_path == file_path
        assert "Processing failed: Test error" in result.errors

    def test_context_manager_sync(self, mock_processing_service):
        """Test synchronous context manager."""
        with AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=False
        ) as processor:
            assert processor is not None
            assert processor._executor is not None

        # Executor should be closed after context exit
        assert processor._executor is None

    @pytest.mark.asyncio
    async def test_context_manager_async(self, mock_processing_service):
        """Test asynchronous context manager."""
        async with AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=True
        ) as processor:
            assert processor is not None

        # Should complete without error

    def test_close_method(self, mock_processing_service):
        """Test resource cleanup."""
        processor = AsyncStatementProcessor(
            processing_service=mock_processing_service, use_asyncio=False
        )

        assert processor._executor is not None

        processor.close()

        assert processor._executor is None

        # Should be safe to call multiple times
        processor.close()


class TestProcessFilesAsync:
    """Test convenience function for async processing."""

    @pytest.fixture
    def mock_processing_service(self):
        """Create mock processing service."""
        service = Mock()

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA, transactions=[])

        validation_result = ValidationResult(is_valid=True, errors=[])

        success_result = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            statement=statement,
            validation_result=validation_result,
            success=True,
            errors=[],
            processing_time=0.1,
        )

        service.process_statement.return_value = success_result
        return service

    @pytest.mark.asyncio
    async def test_process_files_async_convenience(self, mock_processing_service):
        """Test convenience function for async processing."""
        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        result = await process_files_async(
            file_paths=files,
            output_dir=output_dir,
            processing_service=mock_processing_service,
            max_workers=2,
            use_asyncio=True,
        )

        assert isinstance(result, BatchProcessingResult)
        assert result.processing_mode == "asyncio"
        assert len(result.successful_files) == 2
        assert result.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_process_files_async_threading_mode(self, mock_processing_service):
        """Test convenience function in threading mode."""
        files = [Path("file1.pdf")]
        output_dir = Path("output")

        result = await process_files_async(
            file_paths=files,
            output_dir=output_dir,
            processing_service=mock_processing_service,
            max_workers=1,
            use_asyncio=False,
        )

        assert isinstance(result, BatchProcessingResult)
        assert result.processing_mode == "threading"
        assert len(result.successful_files) == 1


class TestAsyncProcessingErrorHandling:
    """Test error handling in async processing."""

    @pytest.fixture
    def failing_processing_service(self):
        """Create processing service that fails."""
        service = Mock()
        service.process_statement.side_effect = Exception("Processing failed")
        return service

    @pytest.mark.asyncio
    async def test_async_processing_with_errors(self, failing_processing_service):
        """Test async processing handles errors gracefully."""
        processor = AsyncStatementProcessor(
            processing_service=failing_processing_service,
            max_workers=1,
            use_asyncio=True,
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        results = []
        async for result in processor.process_batch_async(files, output_dir):
            results.append(result)

        assert len(results) == 2
        assert all(not result.success for result in results)
        assert all("Processing failed" in str(result.errors) for result in results)

    def test_threaded_processing_with_errors(self, failing_processing_service):
        """Test threaded processing handles errors gracefully."""
        processor = AsyncStatementProcessor(
            processing_service=failing_processing_service,
            max_workers=1,
            use_asyncio=False,
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        results = list(processor.process_batch_threaded(files, output_dir))

        assert len(results) == 2
        assert all(not result.success for result in results)

        processor.close()

    @pytest.mark.asyncio
    async def test_batch_complete_with_errors(self, failing_processing_service):
        """Test complete batch processing with errors."""
        processor = AsyncStatementProcessor(
            processing_service=failing_processing_service,
            max_workers=1,
            use_asyncio=True,
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        result = await processor.process_batch_complete(files, output_dir)

        assert len(result.successful_files) == 0
        assert len(result.failed_files) == 2
        assert result.success_rate == 0.0


@pytest.mark.asyncio
async def test_no_deadlock_validation():
    """
    Validate the key requirement: asyncio.run processing two files without deadlock.

    This test specifically validates the Phase 4 → 4.1 requirement:
    "asyncio.run demo processing two files completes without deadlock"
    """
    # Create mock processing service
    service = Mock()

    statement = Statement(payment_method=PaymentMethod.BBVA_VISA, transactions=[])

    validation_result = ValidationResult(is_valid=True, errors=[])

    success_result = ProcessingResult(
        input_path=Path("test.pdf"),
        output_path=Path("output.xlsx"),
        statement=statement,
        validation_result=validation_result,
        success=True,
        errors=[],
        processing_time=0.1,
    )

    service.process_statement.return_value = success_result

    # Create processor
    processor = AsyncStatementProcessor(
        processing_service=service, max_workers=2, use_asyncio=True
    )

    # Process two files - this should complete without deadlock
    files = [Path("file1.pdf"), Path("file2.pdf")]
    output_dir = Path("output")

    # Use asyncio.run equivalent (pytest-asyncio handles this)
    results = []
    async for result in processor.process_batch_async(files, output_dir):
        results.append(result)

    # Validate successful completion without deadlock
    assert len(results) == 2
    assert all(result.success for result in results)

    # Additional validation with complete batch processing
    batch_result = await processor.process_batch_complete(files, output_dir)
    assert batch_result.success_rate == 1.0
    assert len(batch_result.successful_files) == 2


class TestAsyncProcessingErrorCoverage:
    """Test error handling paths to improve coverage."""

    @pytest.mark.asyncio
    async def test_event_publishing_failures(self):
        """Test error handling when event publishing fails."""
        service = Mock()
        service.process_statement.return_value = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            statement=Statement(
                payment_method=PaymentMethod.BBVA_VISA, transactions=[]
            ),
            validation_result=ValidationResult(is_valid=True, errors=[]),
            success=True,
            errors=[],
            processing_time=0.1,
        )

        # Create event publisher that fails
        event_publisher = Mock()
        event_publisher.publish.side_effect = Exception("Event publishing failed")

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=True,
            event_publisher=event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = []
        async for result in processor.process_batch_async(files, output_dir):
            results.append(result)

        # Should still succeed despite event publishing failures
        assert len(results) == 1
        assert results[0].success

    @pytest.mark.asyncio
    async def test_processing_service_exception_in_async(self):
        """Test handling of processing service exceptions in async mode."""
        service = Mock()
        service.process_statement.side_effect = Exception("Service failed")

        event_publisher = Mock()

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=True,
            event_publisher=event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = []
        async for result in processor.process_batch_async(files, output_dir):
            results.append(result)

        assert len(results) == 1
        assert not results[0].success
        assert any(
            "Processing failed: Service failed" in str(result.errors)
            for result in results
        )

    def test_processing_service_exception_in_threading(self):
        """Test handling of processing service exceptions in threading mode."""
        service = Mock()
        service.process_statement.side_effect = Exception("Service failed")

        event_publisher = Mock()

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=False,
            event_publisher=event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = list(processor.process_batch_threaded(files, output_dir))

        assert len(results) == 1
        assert not results[0].success

        processor.close()

    @pytest.mark.asyncio
    async def test_batch_processing_exception(self):
        """Test handling of exceptions during batch processing."""
        service = Mock()
        service.process_statement.side_effect = Exception("Batch error")

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=True,
        )

        files = [Path("file1.pdf"), Path("file2.pdf")]
        output_dir = Path("output")

        # This should handle the exception gracefully
        batch_result = await processor.process_batch_complete(files, output_dir)

        assert len(batch_result.failed_files) == 2
        assert batch_result.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_file_stat_error_handling(self):
        """Test handling of file stat errors during event publishing."""
        service = Mock()
        service.process_statement.return_value = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            statement=Statement(
                payment_method=PaymentMethod.BBVA_VISA, transactions=[]
            ),
            validation_result=ValidationResult(is_valid=True, errors=[]),
            success=True,
            errors=[],
            processing_time=0.1,
        )

        event_publisher = Mock()

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=True,
            event_publisher=event_publisher,
        )

        # Create a path that will cause stat() to fail
        with patch("pathlib.Path.stat", side_effect=OSError("File not found")):
            files = [Path("nonexistent.pdf")]
            output_dir = Path("output")

            results = []
            async for result in processor.process_batch_async(files, output_dir):
                results.append(result)

            # Should still process despite stat error
            assert len(results) == 1

    def test_threaded_event_publishing_with_errors(self):
        """Test event publishing errors in threading mode."""
        service = Mock()
        service.process_statement.return_value = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            statement=Statement(
                payment_method=PaymentMethod.BBVA_VISA, transactions=[]
            ),
            validation_result=ValidationResult(is_valid=True, errors=[]),
            success=True,
            errors=[],
            processing_time=0.1,
        )

        # Event publisher that fails
        event_publisher = Mock()
        event_publisher.publish.side_effect = Exception("Event error")

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=False,
            event_publisher=event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = list(processor.process_batch_threaded(files, output_dir))

        assert len(results) == 1
        assert results[0].success

        processor.close()

    def test_threaded_processing_with_failed_results(self):
        """Test threading mode with failed processing results."""
        service = Mock()
        service.process_statement.return_value = ProcessingResult(
            input_path=Path("test.pdf"),
            output_path=None,
            statement=None,
            validation_result=ValidationResult(is_valid=False, errors=["Failed"]),
            success=False,
            errors=["Processing failed"],
            processing_time=0.1,
        )

        event_publisher = Mock()

        processor = AsyncStatementProcessor(
            processing_service=service,
            max_workers=1,
            use_asyncio=False,
            event_publisher=event_publisher,
        )

        files = [Path("test.pdf")]
        output_dir = Path("output")

        results = list(processor.process_batch_threaded(files, output_dir))

        assert len(results) == 1
        assert not results[0].success

        processor.close()
