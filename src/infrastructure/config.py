import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from domain.models import PaymentMethod


@dataclass
class ProcessingConfig:
    """Processing behavior configuration"""

    max_workers: int = 4
    retry_attempts: int = 3
    enable_validation: bool = True
    enable_balance_checking: bool = True
    duplicate_prefix: str = "DUPLICATED"


@dataclass
class PaymentMethodMappingConfig:
    """Payment method display name mapping configuration"""

    mappings: dict[str, str] = field(default_factory=dict)

    def get_display_name(self, payment_method: PaymentMethod) -> str:
        """
        Get the display name for a payment method.

        Args:
            payment_method: The PaymentMethod enum value

        Returns:
            Custom display name if configured, otherwise the default enum value
        """
        return self.mappings.get(payment_method.name, payment_method.value)


@dataclass
class AmountSignInversionConfig:
    """Amount sign inversion configuration per payment method."""

    invert_all: bool = False
    invert_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    def should_invert(self, payment_method: PaymentMethod) -> bool:
        """Determine if amounts should be inverted for this payment method."""
        method_name = payment_method.name

        # Exclusions take highest priority
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(method_name, pattern):
                return False

        # Check invert patterns
        for pattern in self.invert_patterns:
            if fnmatch.fnmatch(method_name, pattern):
                return True

        return self.invert_all


@dataclass
class OutputConfig:
    """Output format configuration"""

    default_format: str = "excel"
    date_format: str = "%Y-%m-%d"
    decimal_separator: str = ","


@dataclass
class ApplicationConfig:
    """Main application configuration"""

    input_directory: Path
    output_directory: Path
    processing: ProcessingConfig
    output: OutputConfig
    payment_method_mapping: PaymentMethodMappingConfig = field(
        default_factory=PaymentMethodMappingConfig
    )
    amount_sign_inversion: AmountSignInversionConfig = field(
        default_factory=AmountSignInversionConfig
    )
    log_level: str = "INFO"

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ApplicationConfig":
        """Load configuration from YAML file"""
        with open(config_path) as file:
            config_data = yaml.safe_load(file)

        # Parse amount sign inversion config
        inversion_data = config_data.get("amount_sign_inversion", {}) or {}
        amount_sign_inversion = AmountSignInversionConfig(
            invert_all=inversion_data.get("invert_all", False),
            invert_patterns=inversion_data.get("invert_patterns", []) or [],
            exclude_patterns=inversion_data.get("exclude_patterns", []) or [],
        )

        return cls(
            input_directory=Path(config_data["input_directory"]),
            output_directory=Path(config_data["output_directory"]),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            output=OutputConfig(**config_data.get("output", {})),
            payment_method_mapping=PaymentMethodMappingConfig(
                mappings=config_data.get("payment_method_mapping", {}) or {}
            ),
            amount_sign_inversion=amount_sign_inversion,
            log_level=config_data.get("log_level", "INFO"),
        )

    @classmethod
    def from_environment(cls) -> "ApplicationConfig":
        """Load configuration from environment variables"""
        return cls(
            input_directory=Path(os.getenv("FSP_INPUT_DIR", "input")),
            output_directory=Path(os.getenv("FSP_OUTPUT_DIR", "output")),
            processing=ProcessingConfig(
                max_workers=int(os.getenv("FSP_MAX_WORKERS", "4")),
                retry_attempts=int(os.getenv("FSP_RETRY_ATTEMPTS", "3")),
                enable_validation=(
                    os.getenv("FSP_ENABLE_VALIDATION", "true").lower() == "true"
                ),
                enable_balance_checking=(
                    os.getenv("FSP_ENABLE_BALANCE_CHECK", "true").lower() == "true"
                ),
                duplicate_prefix=os.getenv("FSP_DUPLICATE_PREFIX", "DUPLICATED"),
            ),
            output=OutputConfig(
                default_format=os.getenv("FSP_OUTPUT_FORMAT", "excel"),
                date_format=os.getenv("FSP_DATE_FORMAT", "%Y-%m-%d"),
                decimal_separator=os.getenv("FSP_DECIMAL_SEPARATOR", ","),
            ),
            payment_method_mapping=PaymentMethodMappingConfig(
                mappings=cls._load_payment_method_mapping_from_env()
            ),
            amount_sign_inversion=AmountSignInversionConfig(
                invert_all=(
                    os.getenv("FSP_AMOUNT_INVERT_ALL", "false").lower() == "true"
                ),
                invert_patterns=cls._parse_env_list(
                    os.getenv("FSP_AMOUNT_INVERT_PATTERNS", "")
                ),
                exclude_patterns=cls._parse_env_list(
                    os.getenv("FSP_AMOUNT_EXCLUDE_PATTERNS", "")
                ),
            ),
            log_level=os.getenv("FSP_LOG_LEVEL", "INFO"),
        )

    @classmethod
    def _load_payment_method_mapping_from_env(cls) -> dict[str, str]:
        """Load payment method mapping from environment variables"""
        mappings = {}

        # Check for FSP_PAYMENT_METHOD_* environment variables
        for payment_method in PaymentMethod:
            env_var = f"FSP_PAYMENT_METHOD_{payment_method.name}"
            value = os.getenv(env_var)
            if value:
                mappings[payment_method.name] = value

        return mappings

    @classmethod
    def _parse_env_list(cls, env_value: str) -> list[str]:
        """Parse a comma-separated environment variable into a list."""
        if not env_value or not env_value.strip():
            return []
        return [item.strip() for item in env_value.split(",") if item.strip()]
