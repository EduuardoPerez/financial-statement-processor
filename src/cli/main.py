#!/usr/bin/env python3
"""
Click-based CLI interface for Financial Statement Processor.

This module provides a command-line interface for processing financial statements
from various banks. It supports single file processing, batch processing,
validation, and system information display.

Commands:
    info: Display system information and configuration
    process: Process a single statement file
    validate: Validate a statement file without processing
    batch: Process multiple files in a directory
"""

import json
import sys
import traceback
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from application.services import ProcessingResult, StatementProcessingService
from domain.detectors import PaymentMethodDetector
from domain.filename import FilenameGenerator
from domain.models import PaymentMethod
from domain.validation import StatementValidator
from infrastructure.config import ApplicationConfig
from infrastructure.detectors import (
    BBVADetector,
    MacroDetector,
)
from infrastructure.factories import DefaultParserFactory
from infrastructure.repositories import ExcelStatementRepository

__all__ = ["cli"]

# Global console for rich output
console = Console()


class CLIError(Exception):
    """Custom exception for CLI errors."""

    pass


class SimpleFileReader:
    """Simple file reader implementation for CLI."""

    def read(self, path: Path) -> bytes:
        """Read file content as bytes."""
        return path.read_bytes()

    def exists(self, path: Path) -> bool:
        """Check if file exists."""
        return path.exists()


class SimpleFileWriter:
    """Simple file writer implementation for CLI."""

    def write(self, path: Path, content: bytes) -> None:
        """Write content to file."""
        path.write_bytes(content)

    def ensure_directory(self, path: Path) -> None:
        """Ensure directory exists."""
        path.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None) -> ApplicationConfig:
    """Load configuration from file or environment."""
    try:
        if config_path:
            return ApplicationConfig.from_yaml(config_path)
        else:
            return ApplicationConfig.from_environment()
    except Exception as e:
        raise CLIError(f"Failed to load configuration: {str(e)}") from e


def create_components(
    config: ApplicationConfig,
) -> tuple[StatementProcessingService, DefaultParserFactory]:
    """Create and wire up all necessary components."""
    try:
        # Create detector with all bank detectors
        detector = PaymentMethodDetector()
        detector.register_detector(BBVADetector())
        detector.register_detector(MacroDetector())

        # Create parser factory
        parser_factory = DefaultParserFactory(detector)

        # Create file reader and writer implementations
        file_reader = SimpleFileReader()
        file_writer = SimpleFileWriter()

        # Create other components
        validator = StatementValidator()
        filename_generator = FilenameGenerator()
        repository = ExcelStatementRepository(file_reader, file_writer)

        # Create main processing service
        processing_service = StatementProcessingService(
            parser_factory=parser_factory,
            repository=repository,
            validator=validator,
            filename_generator=filename_generator,
        )

        return processing_service, parser_factory

    except Exception as e:
        raise CLIError(f"Failed to initialize components: {str(e)}") from e


def output_json(data: dict[str, Any]) -> None:
    """Output data as JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def output_error(
    message: str, verbose: bool = False, exception: Exception | None = None
) -> None:
    """Output error message with optional verbose details."""
    if verbose and exception:
        console.print(f"[red]❌ Error: {message}[/red]")
        console.print("\n[yellow]Full Error Details:[/yellow]")
        console.print(traceback.format_exc())
    else:
        console.print(f"[red]❌ Error: {message}[/red]")


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose logging and full stack traces"
)
@click.pass_context
def cli(ctx: click.Context, config: Path | None, verbose: bool) -> None:
    """Financial Statement Processor CLI."""
    ctx.ensure_object(dict)

    try:
        # Load configuration
        app_config = load_config(config)
        if verbose:
            app_config.log_level = "DEBUG"

        # Store in context
        ctx.obj["config"] = app_config
        ctx.obj["verbose"] = verbose

    except CLIError as e:
        if verbose:
            output_error(str(e), verbose=True, exception=e)
        else:
            output_error(str(e))
        sys.exit(1)
    except Exception as e:
        output_error(f"Unexpected error: {str(e)}", verbose=verbose, exception=e)
        sys.exit(1)


@cli.command()
@click.option("--json", "output_json_flag", is_flag=True, help="Output in JSON format")
@click.pass_context
def info(ctx: click.Context, output_json_flag: bool) -> None:
    """Show system information and configuration."""
    try:
        config: ApplicationConfig = ctx.obj["config"]

        # Create components to get supported extensions
        _, parser_factory = create_components(config)
        supported_extensions = sorted(parser_factory.get_supported_extensions())

        # Supported payment methods
        supported_methods = [method.value for method in PaymentMethod]

        info_data = {
            "version": "0.1.0",
            "config": {
                "input_directory": str(config.input_directory),
                "output_directory": str(config.output_directory),
                "log_level": config.log_level,
                "async_processing": config.enable_async,
                "max_workers": config.processing.max_workers,
                "default_format": config.output.default_format,
                "enable_validation": config.processing.enable_validation,
                "enable_balance_checking": config.processing.enable_balance_checking,
            },
            "supported_banks": supported_methods,
            "supported_extensions": supported_extensions,
        }

        if output_json_flag:
            output_json(info_data)
        else:
            # Rich formatted output
            console.print(
                Panel.fit(
                    "[bold blue]Financial Statement Processor[/bold blue]",
                    title="v0.1.0",
                )
            )

            # Configuration table
            config_table = Table(title="Configuration")
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="magenta")

            config_table.add_row("Input Directory", str(config.input_directory))
            config_table.add_row("Output Directory", str(config.output_directory))
            config_table.add_row("Log Level", config.log_level)
            config_table.add_row("Async Processing", str(config.enable_async))
            config_table.add_row("Max Workers", str(config.processing.max_workers))
            config_table.add_row("Default Format", config.output.default_format)
            config_table.add_row(
                "Enable Validation", str(config.processing.enable_validation)
            )
            config_table.add_row(
                "Enable Balance Checking",
                str(config.processing.enable_balance_checking),
            )

            console.print(config_table)

            # Supported banks
            console.print("\n[bold green]Supported Banks:[/bold green]")
            for method in supported_methods:
                console.print(f"  • {method}")

            # Supported formats
            console.print(
                f"\n[bold green]Supported Formats:[/bold green] {', '.join(supported_extensions)}"
            )

    except Exception as e:
        output_error(
            f"Failed to display info: {str(e)}", verbose=ctx.obj["verbose"], exception=e
        )
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["excel", "csv", "json"]),
    default="excel",
    help="Output format",
)
@click.option(
    "--json", "output_json_flag", is_flag=True, help="Output result in JSON format"
)
@click.pass_context
def process(
    ctx: click.Context,
    input_file: Path,
    output: Path | None,
    format: str,
    output_json_flag: bool,
) -> None:
    """Process a single statement file."""
    try:
        config: ApplicationConfig = ctx.obj["config"]

        # Create components
        processing_service, _ = create_components(config)

        # Determine output path
        if output:
            output_path = output.parent
        else:
            output_path = config.output_directory

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        # Process with progress indication
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Processing {input_file.name}...", total=None)

            result: ProcessingResult = processing_service.process_statement(
                input_file, output_path
            )

            progress.update(task, completed=True)

        if result.success:
            result_data = {
                "success": True,
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "transaction_count": (
                    len(result.statement.transactions) if result.statement else 0
                ),
                "processing_time": result.processing_time,
            }

            if output_json_flag:
                output_json(result_data)
            else:
                console.print(
                    f"[green]✅ Successfully processed {input_file.name}[/green]"
                )
                console.print(f"   Output: {result.output_path}")
                console.print(
                    f"   Transactions: {len(result.statement.transactions) if result.statement else 0}"
                )
                console.print(f"   Processing time: {result.processing_time:.2f}s")
        else:
            error_data = {
                "success": False,
                "input_file": str(input_file),
                "errors": result.errors,
                "processing_time": result.processing_time,
            }

            if output_json_flag:
                output_json(error_data)
            else:
                console.print(f"[red]❌ Failed to process {input_file.name}[/red]")
                for error in result.errors:
                    console.print(f"   • {error}")

            sys.exit(1)

    except Exception as e:
        output_error(
            f"Processing failed: {str(e)}", verbose=ctx.obj["verbose"], exception=e
        )
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--quick", is_flag=True, help="Show only pass/fail status")
@click.option(
    "--json", "output_json_flag", is_flag=True, help="Output result in JSON format"
)
@click.pass_context
def validate(
    ctx: click.Context, input_file: Path, quick: bool, output_json_flag: bool
) -> None:
    """Validate a statement file without processing."""
    try:
        config: ApplicationConfig = ctx.obj["config"]

        # Create components
        processing_service, _ = create_components(config)

        # Create a temporary output directory for validation
        temp_output = Path("temp_validation")
        temp_output.mkdir(exist_ok=True)

        # Process file to get validation results
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Validating {input_file.name}...", total=None)

            result: ProcessingResult = processing_service.process_statement(
                input_file, temp_output
            )

            progress.update(task, completed=True)

        # Clean up temp file if created
        if result.output_path and result.output_path.exists():
            result.output_path.unlink()
        temp_output.rmdir()

        validation_data = {
            "valid": result.success and result.validation_result.is_valid,
            "input_file": str(input_file),
            "transaction_count": (
                len(result.statement.transactions) if result.statement else 0
            ),
            "errors": (
                result.validation_result.errors
                if result.validation_result
                else result.errors
            ),
            "processing_time": result.processing_time,
        }

        if result.statement:
            validation_data.update(
                {
                    "balance_ars": float(result.statement.get_balance().ars_amount),
                    "balance_usd": float(result.statement.get_balance().usd_amount),
                    "payment_method": result.statement.payment_method.value,
                    "transaction_count": len(result.statement.transactions),
                }
            )

        if output_json_flag:
            output_json(validation_data)
        else:
            if quick:
                # Quick validation output
                status = "✅ VALID" if validation_data["valid"] else "❌ INVALID"
                console.print(
                    f"{status} - {validation_data['transaction_count']} transactions"
                )
            else:
                # Detailed validation output
                status_color = "green" if validation_data["valid"] else "red"
                status_icon = "✅" if validation_data["valid"] else "❌"

                console.print(
                    f"[{status_color}]{status_icon} Validation Results for {input_file.name}[/{status_color}]"
                )
                console.print(
                    f"   Status: {'VALID' if validation_data['valid'] else 'INVALID'}"
                )
                console.print(
                    f"   Transactions: {validation_data['transaction_count']}"
                )

                if result.statement:
                    console.print(
                        f"   Payment Method: {result.statement.payment_method.value}"
                    )
                    console.print(
                        f"   Balance: ARS {validation_data['balance_ars']:.2f}, USD {validation_data['balance_usd']:.2f}"
                    )

                console.print(
                    f"   Validation Time: {validation_data['processing_time']:.2f}s"
                )

                if not validation_data["valid"] and validation_data["errors"]:
                    console.print("\n[red]Validation Errors:[/red]")
                    errors = validation_data["errors"]
                    if isinstance(errors, list):
                        for error in errors:
                            console.print(f"   • {error}")

        if not validation_data["valid"]:
            sys.exit(1)

    except Exception as e:
        output_error(
            f"Validation failed: {str(e)}", verbose=ctx.obj["verbose"], exception=e
        )
        sys.exit(1)


@cli.command()
@click.argument(
    "input_directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--output-dir", "-o", type=click.Path(path_type=Path), help="Output directory"
)
@click.option(
    "--json", "output_json_flag", is_flag=True, help="Output result in JSON format"
)
@click.pass_context
def batch(
    ctx: click.Context,
    input_directory: Path,
    output_dir: Path | None,
    output_json_flag: bool,
) -> None:
    """Process multiple statement files in a directory."""
    try:
        config: ApplicationConfig = ctx.obj["config"]

        # Create components
        processing_service, parser_factory = create_components(config)

        # Determine output directory
        if output_dir:
            output_path = output_dir
        else:
            output_path = config.output_directory

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all supported files
        supported_extensions = parser_factory.get_supported_extensions()
        files: list[Path] = []
        for ext in supported_extensions:
            files.extend(input_directory.glob(f"*{ext}"))
            files.extend(input_directory.glob(f"*{ext.upper()}"))

        files = sorted(set(files))  # Remove duplicates and sort

        if not files:
            console.print(
                f"[yellow]No supported files found in {input_directory}[/yellow]"
            )
            console.print(f"Supported extensions: {', '.join(supported_extensions)}")
            return

        # Process files with progress bar
        successful_files = []
        failed_files = []
        total_transactions = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing {len(files)} files...", total=len(files)
            )

            for i, file_path in enumerate(files):
                progress.update(task, description=f"Processing {file_path.name}...")

                try:
                    result = processing_service.process_statement(
                        file_path, output_path
                    )

                    if result.success and result.statement:
                        successful_files.append(
                            {
                                "file": str(file_path),
                                "output": str(result.output_path),
                                "transactions": len(result.statement.transactions),
                                "processing_time": result.processing_time,
                            }
                        )
                        total_transactions += len(result.statement.transactions)
                    else:
                        failed_files.append(
                            {"file": str(file_path), "errors": result.errors}
                        )

                except Exception as e:
                    failed_files.append({"file": str(file_path), "errors": [str(e)]})

                progress.update(task, advance=1)

        # Results
        batch_data = {
            "total_files": len(files),
            "successful": len(successful_files),
            "failed": len(failed_files),
            "total_transactions": total_transactions,
            "successful_files": successful_files,
            "failed_files": failed_files,
        }

        if output_json_flag:
            output_json(batch_data)
        else:
            console.print("\n[bold green]✅ Batch Processing Complete[/bold green]")
            console.print(f"   Processed: {len(successful_files)}/{len(files)} files")
            console.print(f"   Failed: {len(failed_files)}/{len(files)} files")
            console.print(f"   Total Transactions: {total_transactions}")

            if failed_files:
                console.print("\n[red]Failed Files:[/red]")
                for failed in failed_files:
                    file_path = Path(str(failed["file"]))
                    errors = failed["errors"]
                    error_str = (
                        ", ".join(str(e) for e in errors)
                        if isinstance(errors, list)
                        else str(errors)
                    )
                    console.print(f"   • {file_path.name}: {error_str}")

        if failed_files:
            sys.exit(1)

    except Exception as e:
        output_error(
            f"Batch processing failed: {str(e)}",
            verbose=ctx.obj["verbose"],
            exception=e,
        )
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
