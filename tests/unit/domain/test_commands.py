"""Unit tests for Command Pattern implementation."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.commands import (
    BatchProcessCommand,
    Command,
    CommandResult,
    ProcessStatementCommand,
)


class TestCommandResult:
    """Test CommandResult dataclass functionality."""

    def test_command_result_creation_success(self):
        """Test creating a successful CommandResult."""
        result = CommandResult(
            success=True,
            message="Operation completed successfully",
            data={"transactions": 45},
            execution_time=1.23,
            errors=[],
        )

        assert result.success is True
        assert result.message == "Operation completed successfully"
        assert result.data == {"transactions": 45}
        assert result.execution_time == 1.23
        assert result.errors == []

    def test_command_result_creation_failure(self):
        """Test creating a failed CommandResult."""
        result = CommandResult(
            success=False,
            message="Operation failed",
            execution_time=0.5,
            errors=["File not found", "Invalid format"],
        )

        assert result.success is False
        assert result.message == "Operation failed"
        assert result.data is None  # Default value
        assert result.execution_time == 0.5
        assert result.errors == ["File not found", "Invalid format"]

    def test_command_result_default_values(self):
        """Test CommandResult with minimal parameters."""
        result = CommandResult(success=True, message="Test")

        assert result.success is True
        assert result.message == "Test"
        assert result.data is None
        assert result.execution_time == 0.0
        assert result.errors == []


class TestCommand:
    """Test Command abstract base class."""

    def test_command_is_abstract(self):
        """Test that Command cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Command()

    def test_command_subclass_must_implement_methods(self):
        """Test that Command subclasses must implement all abstract methods."""

        class IncompleteCommand(Command):
            def execute(self):
                return CommandResult(success=True, message="Test")

            # Missing undo() and can_undo()

        with pytest.raises(TypeError):
            IncompleteCommand()

    def test_command_complete_implementation(self):
        """Test that complete Command implementation can be instantiated."""

        class CompleteCommand(Command):
            def execute(self):
                return CommandResult(success=True, message="Test")

            def undo(self):
                pass

            def can_undo(self):
                return False

        command = CompleteCommand()
        assert isinstance(command, Command)
        result = command.execute()
        assert result.success is True


class TestProcessStatementCommand:
    """Test ProcessStatementCommand implementation."""

    @pytest.fixture
    def mock_processing_service(self):
        """Create a mock processing service."""
        service = Mock()

        # Create a mock result
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = Path("output/test-transactions.xlsx")
        mock_result.errors = []

        service.process_statement.return_value = mock_result
        return service

    @pytest.fixture
    def process_command(self, mock_processing_service):
        """Create a ProcessStatementCommand for testing."""
        return ProcessStatementCommand(
            input_path=Path("input/test.pdf"),
            output_dir=Path("output"),
            processing_service=mock_processing_service,
        )

    def test_process_statement_command_initialization(self, mock_processing_service):
        """Test ProcessStatementCommand initialization."""
        input_path = Path("input/statement.pdf")
        output_dir = Path("output")

        command = ProcessStatementCommand(
            input_path=input_path,
            output_dir=output_dir,
            processing_service=mock_processing_service,
        )

        assert command._input_path == input_path
        assert command._output_dir == output_dir
        assert command._processing_service == mock_processing_service
        assert command._result is None

    def test_execute_success(self, process_command, mock_processing_service):
        """Test successful command execution."""
        result = process_command.execute()

        assert result.success is True
        assert "Successfully processed test.pdf" in result.message
        assert result.data is not None
        assert result.execution_time > 0
        assert result.errors == []

        # Verify service was called correctly
        mock_processing_service.process_statement.assert_called_once_with(
            Path("input/test.pdf"), Path("output")
        )

    def test_execute_processing_service_failure(self, mock_processing_service):
        """Test command execution when processing service fails."""
        # Configure mock to return failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.errors = ["Parsing failed"]
        mock_processing_service.process_statement.return_value = mock_result

        command = ProcessStatementCommand(
            input_path=Path("input/test.pdf"),
            output_dir=Path("output"),
            processing_service=mock_processing_service,
        )

        result = command.execute()

        assert result.success is False
        assert "Processing failed for test.pdf" in result.message
        assert result.data == mock_result
        assert result.execution_time > 0
        assert result.errors == ["Parsing failed"]

    def test_execute_exception_handling(self, mock_processing_service):
        """Test command execution when service raises exception."""
        # Configure mock to raise exception
        mock_processing_service.process_statement.side_effect = Exception(
            "Service error"
        )

        command = ProcessStatementCommand(
            input_path=Path("input/test.pdf"),
            output_dir=Path("output"),
            processing_service=mock_processing_service,
        )

        result = command.execute()

        assert result.success is False
        assert "Failed to process test.pdf: Service error" in result.message
        assert result.data is None
        assert result.execution_time > 0
        assert result.errors == ["Service error"]

    def test_can_undo_with_result(self, process_command):
        """Test can_undo returns True when result exists with output path."""
        # Execute command to create result
        process_command.execute()

        assert process_command.can_undo() is True

    def test_can_undo_without_result(self, process_command):
        """Test can_undo returns False when no result exists."""
        assert process_command.can_undo() is False

    def test_can_undo_with_result_no_output_path(self, mock_processing_service):
        """Test can_undo returns False when result has no output path."""
        # Configure mock result without output_path
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = None
        mock_processing_service.process_statement.return_value = mock_result

        command = ProcessStatementCommand(
            input_path=Path("input/test.pdf"),
            output_dir=Path("output"),
            processing_service=mock_processing_service,
        )

        command.execute()
        assert command.can_undo() is False

    def test_undo_removes_output_file(self, process_command, tmp_path):
        """Test undo removes the generated output file."""
        # Create a temporary output file
        output_file = tmp_path / "test-output.xlsx"
        output_file.write_text("test content")
        assert output_file.exists()

        # Mock the result to point to our temporary file
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = output_file
        process_command._result = mock_result

        # Execute undo
        process_command.undo()

        # Verify file was removed
        assert not output_file.exists()

    def test_undo_no_result(self, process_command):
        """Test undo does nothing when no result exists."""
        # Should not raise exception
        process_command.undo()

    def test_undo_file_does_not_exist(self, process_command):
        """Test undo handles case where output file doesn't exist."""
        # Mock result with non-existent file
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = Path("non-existent-file.xlsx")
        process_command._result = mock_result

        # Should not raise exception
        process_command.undo()


class TestBatchProcessCommand:
    """Test BatchProcessCommand implementation."""

    @pytest.fixture
    def mock_commands(self):
        """Create mock commands for testing."""
        commands = []
        for i in range(3):
            command = Mock(spec=Command)
            command.execute.return_value = CommandResult(
                success=True, message=f"Command {i + 1} successful", execution_time=0.1
            )
            command.can_undo.return_value = True
            command.undo.return_value = None
            commands.append(command)
        return commands

    def test_batch_command_initialization(self, mock_commands):
        """Test BatchProcessCommand initialization."""
        batch_command = BatchProcessCommand(mock_commands)

        assert batch_command._commands == mock_commands
        assert batch_command._executed_commands == []

    def test_execute_all_commands_successful(self, mock_commands):
        """Test batch execution when all commands succeed."""
        batch_command = BatchProcessCommand(mock_commands)
        result = batch_command.execute()

        assert result.success is True
        assert "3/3 commands successful" in result.message
        assert result.data["success_count"] == 3
        assert result.data["total_count"] == 3
        assert result.data["success_rate"] == 1.0
        assert len(result.data["individual_results"]) == 3
        assert result.errors == []
        assert result.execution_time > 0

        # Verify all commands were executed
        for command in mock_commands:
            command.execute.assert_called_once()

    def test_execute_with_command_failure(self, mock_commands):
        """Test batch execution when one command fails."""
        # Make second command fail
        mock_commands[1].execute.return_value = CommandResult(
            success=False, message="Command 2 failed", errors=["Test error"]
        )

        batch_command = BatchProcessCommand(mock_commands)
        result = batch_command.execute()

        assert result.success is False
        assert "1/3 commands successful" in result.message
        assert result.data["success_count"] == 1
        assert result.data["total_count"] == 3
        assert result.data["success_rate"] == 1 / 3
        assert len(result.errors) == 1
        assert "Command 2 failed: Command 2 failed" in result.errors[0]

        # Verify only first two commands were executed
        mock_commands[0].execute.assert_called_once()
        mock_commands[1].execute.assert_called_once()
        mock_commands[2].execute.assert_not_called()

        # Verify first command was undone (rollback)
        mock_commands[0].undo.assert_called_once()

    def test_execute_with_exception(self, mock_commands):
        """Test batch execution when command raises exception."""
        # Make first command raise exception
        mock_commands[0].execute.side_effect = Exception("Unexpected error")

        batch_command = BatchProcessCommand(mock_commands)
        result = batch_command.execute()

        assert result.success is False
        assert "Batch processing failed with unexpected error" in result.message
        assert result.data["success_count"] == 0
        assert result.data["total_count"] == 3
        assert result.errors == ["Unexpected error"]

    def test_can_undo_with_executed_commands(self, mock_commands):
        """Test can_undo returns True when commands have been executed."""
        batch_command = BatchProcessCommand(mock_commands)
        batch_command.execute()

        assert batch_command.can_undo() is True

    def test_can_undo_without_executed_commands(self, mock_commands):
        """Test can_undo returns False when no commands executed."""
        batch_command = BatchProcessCommand(mock_commands)

        assert batch_command.can_undo() is False

    def test_undo_reverses_executed_commands(self, mock_commands):
        """Test undo calls undo on all executed commands in reverse order."""
        batch_command = BatchProcessCommand(mock_commands)
        batch_command.execute()

        # Clear previous undo calls from rollback during execution
        for command in mock_commands:
            command.undo.reset_mock()

        batch_command.undo()

        # Verify all commands were undone in reverse order
        for command in mock_commands:
            command.undo.assert_called_once()

        # Verify executed commands list is cleared
        assert batch_command._executed_commands == []

    def test_undo_handles_undo_exceptions(self, mock_commands):
        """Test undo continues even if individual command undo fails."""
        # Make one command's undo raise exception
        mock_commands[1].undo.side_effect = Exception("Undo failed")

        batch_command = BatchProcessCommand(mock_commands)
        batch_command.execute()

        # Clear previous undo calls
        for command in mock_commands:
            command.undo.reset_mock()

        # Should not raise exception
        batch_command.undo()

        # Verify all commands' undo was attempted
        for command in mock_commands:
            command.undo.assert_called_once()

    def test_undo_skips_commands_that_cannot_undo(self, mock_commands):
        """Test undo skips commands that return False for can_undo."""
        # Make middle command unable to undo
        mock_commands[1].can_undo.return_value = False

        batch_command = BatchProcessCommand(mock_commands)
        batch_command.execute()

        # Clear previous undo calls
        for command in mock_commands:
            command.undo.reset_mock()

        batch_command.undo()

        # Verify only commands that can undo were undone
        mock_commands[0].undo.assert_called_once()
        mock_commands[1].undo.assert_not_called()  # Cannot undo
        mock_commands[2].undo.assert_called_once()

    def test_empty_command_list(self):
        """Test batch command with empty command list."""
        batch_command = BatchProcessCommand([])
        result = batch_command.execute()

        assert result.success is True
        assert "0/0 commands successful" in result.message
        assert result.data["success_count"] == 0
        assert result.data["total_count"] == 0
        assert result.data["success_rate"] == 0.0
        assert result.errors == []


class TestCommandIntegration:
    """Integration tests for Command Pattern components."""

    def test_process_statement_command_validation_requirement(self):
        """Test the specific validation requirement from Prompt 22."""
        # Create a mock processing service that returns success
        mock_service = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = Path("output/test.xlsx")
        mock_result.errors = []
        mock_service.process_statement.return_value = mock_result

        # Create and execute command
        command = ProcessStatementCommand(
            input_path=Path("test.pdf"),
            output_dir=Path("output"),
            processing_service=mock_service,
        )

        result = command.execute()

        # Validation requirement: ProcessStatementCommand(...).execute().success is True
        assert result.success is True

    def test_command_pattern_workflow(self):
        """Test complete command pattern workflow."""
        # Create mock processing service
        mock_service = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = Path("output/test.xlsx")
        mock_service.process_statement.return_value = mock_result

        # Create individual commands
        commands = [
            ProcessStatementCommand(
                input_path=Path(f"file{i}.pdf"),
                output_dir=Path("output"),
                processing_service=mock_service,
            )
            for i in range(3)
        ]

        # Create batch command
        batch_command = BatchProcessCommand(commands)

        # Execute batch
        result = batch_command.execute()

        # Verify batch success
        assert result.success is True
        assert result.data["success_count"] == 3

        # Verify can undo
        assert batch_command.can_undo() is True

        # Test undo
        batch_command.undo()
        assert batch_command.can_undo() is False
