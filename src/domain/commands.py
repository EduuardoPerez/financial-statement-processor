"""Command Pattern implementation for financial statement processing operations.

This module implements the Command Pattern to encapsulate operations as objects,
enabling undo functionality, logging, queuing, and transactional batch processing.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    """Result of command execution with comprehensive details.

    Attributes:
        success: Whether the command executed successfully
        message: Human-readable description of the result
        data: Optional data payload from command execution
        execution_time: Time taken to execute the command in seconds
        errors: List of error messages if any occurred
    """

    success: bool
    message: str
    data: Any = None
    execution_time: float = 0.0
    errors: list[str] = field(default_factory=list)


class Command(ABC):
    """Abstract command interface following Command Pattern.

    Commands encapsulate operations as objects, enabling:
    - Undo/redo functionality
    - Operation logging and auditing
    - Queuing and batch processing
    - Transactional operations with rollback
    """

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return comprehensive result.

        Returns:
            CommandResult with success status, message, data, and timing
        """
        pass

    @abstractmethod
    def undo(self) -> None:
        """Undo the command if possible.

        Should reverse the effects of execute() when can_undo() returns True.
        """
        pass

    @abstractmethod
    def can_undo(self) -> bool:
        """Check if command can be undone.

        Returns:
            True if undo() can be called safely, False otherwise
        """
        pass


class ProcessStatementCommand(Command):
    """Command to process a single financial statement file.

    This command encapsulates the complete workflow of processing a statement:
    - Parsing the input file
    - Validating the statement
    - Generating output filename
    - Saving to Excel format

    Supports undo by removing the generated output file.
    """

    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        processing_service: Any,  # StatementProcessingService - avoiding circular import
    ):
        """Initialize command with processing parameters.

        Args:
            input_path: Path to the input statement file
            output_dir: Directory where output file should be saved
            processing_service: Service to handle the actual processing
        """
        self._input_path = input_path
        self._output_dir = output_dir
        self._processing_service = processing_service
        self._result: Any | None = None  # ProcessingResult - avoiding circular import

    def execute(self) -> CommandResult:
        """Execute statement processing with comprehensive error handling and timing.

        Returns:
            CommandResult with success status and processing details
        """
        start_time = time.time()

        try:
            # Execute the statement processing
            self._result = self._processing_service.process_statement(
                self._input_path, self._output_dir
            )

            execution_time = time.time() - start_time

            # Check if processing was successful
            if self._result.success:
                return CommandResult(
                    success=True,
                    message=f"Successfully processed {self._input_path.name}",
                    data=self._result,
                    execution_time=execution_time,
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Processing failed for {self._input_path.name}",
                    data=self._result,
                    execution_time=execution_time,
                    errors=(
                        self._result.errors if hasattr(self._result, "errors") else []
                    ),
                )

        except Exception as e:
            execution_time = time.time() - start_time

            return CommandResult(
                success=False,
                message=f"Failed to process {self._input_path.name}: {str(e)}",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def undo(self) -> None:
        """Remove generated output file if it exists.

        This undoes the effect of execute() by deleting the output file
        that was created during processing.
        """
        if self._result and hasattr(self._result, "output_path"):
            output_path = self._result.output_path
            if output_path and output_path.exists():
                output_path.unlink()

    def can_undo(self) -> bool:
        """Check if command can be undone.

        Returns:
            True if a result exists with an output path, False otherwise
        """
        return (
            self._result is not None
            and hasattr(self._result, "output_path")
            and self._result.output_path is not None
        )


class BatchProcessCommand(Command):
    """Command to process multiple statements with transactional rollback capability.

    This command executes a batch of ProcessStatementCommand instances:
    - Executes commands sequentially
    - Tracks successfully executed commands
    - Rolls back all successful commands if any command fails
    - Provides comprehensive batch processing results
    """

    def __init__(self, commands: list[Command]):
        """Initialize batch command with list of commands to execute.

        Args:
            commands: List of Command instances to execute in batch
        """
        self._commands = commands
        self._executed_commands: list[Command] = []

    def execute(self) -> CommandResult:
        """Execute batch processing with rollback on failure.

        Executes all commands sequentially. If any command fails,
        all previously successful commands are rolled back.

        Returns:
            CommandResult with batch processing summary
        """
        results = []
        start_time = time.time()
        success_count = 0

        try:
            for command in self._commands:
                result = command.execute()
                results.append(result)

                if result.success:
                    self._executed_commands.append(command)
                    success_count += 1
                else:
                    # Stop on first failure and rollback
                    self.undo()
                    break

            execution_time = time.time() - start_time
            total_commands = len(self._commands)
            all_successful = success_count == total_commands

            return CommandResult(
                success=all_successful,
                message=f"Batch processing: {success_count}/{total_commands} commands successful",
                data={
                    "individual_results": results,
                    "success_count": success_count,
                    "total_count": total_commands,
                    "success_rate": (
                        success_count / total_commands if total_commands > 0 else 0.0
                    ),
                },
                execution_time=execution_time,
                errors=[
                    f"Command {i + 1} failed: {result.message}"
                    for i, result in enumerate(results)
                    if not result.success
                ],
            )

        except Exception as e:
            execution_time = time.time() - start_time
            # Rollback on unexpected error
            self.undo()

            return CommandResult(
                success=False,
                message=f"Batch processing failed with unexpected error: {str(e)}",
                data={
                    "individual_results": results,
                    "success_count": success_count,
                    "total_count": len(self._commands),
                },
                execution_time=execution_time,
                errors=[str(e)],
            )

    def undo(self) -> None:
        """Undo all successfully executed commands in reverse order.

        This provides transactional rollback capability for batch operations.
        Commands are undone in reverse order to maintain consistency.
        """
        for command in reversed(self._executed_commands):
            if command.can_undo():
                try:
                    command.undo()
                except Exception:
                    # Log error but continue with rollback
                    # In a real implementation, this would use proper logging
                    pass

        self._executed_commands.clear()

    def can_undo(self) -> bool:
        """Check if batch command can be undone.

        Returns:
            True if any commands have been executed, False otherwise
        """
        return len(self._executed_commands) > 0
