"""
Repository abstractions for the Financial Statement Processor.

This module defines the abstract interfaces (ports) for data access operations
in our hexagonal architecture. These abstractions will be implemented by
concrete adapters in the infrastructure layer.

Classes:
    FileReader: Protocol for file reading operations
    FileWriter: Protocol for file writing operations
    StatementRepository: Abstract repository for statement persistence
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from .models import Statement


class FileReader(Protocol):
    """Protocol for file reading operations."""

    def read(self, path: Path) -> bytes:
        """
        Read the contents of a file.

        Args:
            path: Path to the file to read

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
        """
        ...

    def exists(self, path: Path) -> bool:
        """
        Check if a file exists.

        Args:
            path: Path to check

        Returns:
            True if the file exists, False otherwise
        """
        ...


class FileWriter(Protocol):
    """Protocol for file writing operations."""

    def write(self, path: Path, content: bytes) -> None:
        """
        Write content to a file.

        Args:
            path: Path to write to
            content: Content to write as bytes

        Raises:
            PermissionError: If the file cannot be written
            OSError: If there's an I/O error during writing
        """
        ...

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure that a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure exists

        Raises:
            PermissionError: If the directory cannot be created
            OSError: If there's an error creating the directory
        """
        ...


class StatementRepository(ABC):
    """Abstract repository for statement persistence."""

    @abstractmethod
    def save_statement(self, statement: Statement, output_path: Path) -> None:
        """
        Save statement to specified path.

        Args:
            statement: The statement to save
            output_path: Path where the statement should be saved

        Raises:
            ValueError: If the statement is invalid
            OSError: If there's an error writing the file
        """
        ...

    @abstractmethod
    def load_raw_data(self, input_path: Path) -> bytes:
        """
        Load raw data from input file.

        Args:
            input_path: Path to the input file

        Returns:
            Raw file data as bytes

        Raises:
            FileNotFoundError: If the input file does not exist
            PermissionError: If the file cannot be read
            OSError: If there's an I/O error during reading
        """
        ...
