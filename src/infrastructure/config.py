import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class DatabaseConfig:
    """Database connection configuration"""

    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 5


@dataclass
class ProcessingConfig:
    """Processing behavior configuration"""

    max_workers: int = 4
    chunk_size: int = 1000
    timeout_seconds: int = 300
    retry_attempts: int = 3
    enable_validation: bool = True
    enable_balance_checking: bool = True


@dataclass
class OutputConfig:
    """Output format configuration"""

    default_format: str = "excel"
    excel_sheet_name: str = "Sheet1"
    csv_delimiter: str = ","
    include_index: bool = False
    date_format: str = "%Y-%m-%d"


@dataclass
class ApplicationConfig:
    """Main application configuration"""

    input_directory: Path
    output_directory: Path
    processing: ProcessingConfig
    output: OutputConfig
    database: DatabaseConfig | None = None
    log_level: str = "INFO"
    enable_async: bool = False

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ApplicationConfig":
        """Load configuration from YAML file"""
        with open(config_path) as file:
            config_data = yaml.safe_load(file)

        return cls(
            input_directory=Path(config_data["input_directory"]),
            output_directory=Path(config_data["output_directory"]),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            output=OutputConfig(**config_data.get("output", {})),
            database=(
                DatabaseConfig(**config_data["database"])
                if "database" in config_data
                else None
            ),
            log_level=config_data.get("log_level", "INFO"),
            enable_async=config_data.get("enable_async", False),
        )

    @classmethod
    def from_environment(cls) -> "ApplicationConfig":
        """Load configuration from environment variables"""
        return cls(
            input_directory=Path(os.getenv("FSP_INPUT_DIR", "input")),
            output_directory=Path(os.getenv("FSP_OUTPUT_DIR", "output")),
            processing=ProcessingConfig(
                max_workers=int(os.getenv("FSP_MAX_WORKERS", "4")),
                chunk_size=int(os.getenv("FSP_CHUNK_SIZE", "1000")),
                timeout_seconds=int(os.getenv("FSP_TIMEOUT", "300")),
                retry_attempts=int(os.getenv("FSP_RETRY_ATTEMPTS", "3")),
                enable_validation=(
                    os.getenv("FSP_ENABLE_VALIDATION", "true").lower() == "true"
                ),
                enable_balance_checking=(
                    os.getenv("FSP_ENABLE_BALANCE_CHECK", "true").lower() == "true"
                ),
            ),
            output=OutputConfig(
                default_format=os.getenv("FSP_OUTPUT_FORMAT", "excel"),
                excel_sheet_name=os.getenv("FSP_EXCEL_SHEET", "Sheet1"),
                csv_delimiter=os.getenv("FSP_CSV_DELIMITER", ","),
                include_index=(
                    os.getenv("FSP_INCLUDE_INDEX", "false").lower() == "true"
                ),
                date_format=os.getenv("FSP_DATE_FORMAT", "%Y-%m-%d"),
            ),
            database=(
                cls._load_database_from_env() if os.getenv("FSP_DB_HOST") else None
            ),
            log_level=os.getenv("FSP_LOG_LEVEL", "INFO"),
            enable_async=(os.getenv("FSP_ENABLE_ASYNC", "false").lower() == "true"),
        )

    @classmethod
    def _load_database_from_env(cls) -> DatabaseConfig | None:
        """Load database configuration from environment variables"""
        host = os.getenv("FSP_DB_HOST")
        if not host:
            return None

        return DatabaseConfig(
            host=host,
            port=int(os.getenv("FSP_DB_PORT", "5432")),
            database=os.getenv("FSP_DB_NAME", "financial_statements"),
            username=os.getenv("FSP_DB_USER", "fsp_user"),
            password=os.getenv("FSP_DB_PASSWORD", ""),
            pool_size=int(os.getenv("FSP_DB_POOL_SIZE", "5")),
        )
