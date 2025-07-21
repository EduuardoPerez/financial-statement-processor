# Payment Method Display Name Mapping

The Financial Statement Processor now supports customizing payment method display names in the generated Excel reports through configuration.

## Overview

By default, the system uses the built-in PaymentMethod enum values:

- `MACRO_VISA` → "Macro Visa"
- `BBVA_VISA` → "BBVA Visa"
- `BBVA_MASTERCARD` → "BBVA Mastercard"
- `BBVA_ACCOUNT` → "BBVA Account"
- `MACRO_ACCOUNT` → "Macro Account"
- `MERCADOPAGO` → "Mercado Pago"

You can now customize these display names in the Excel output without affecting the core business logic.

## Configuration Methods

### 1. YAML Configuration

Add a `payment_method_mapping` section to your YAML config file:

```yaml
# config/development.yaml
payment_method_mapping:
  MACRO_VISA: "MACRO VISA"           # Override default "Macro Visa"
  BBVA_VISA: "BBVA VISA"             # Override default "BBVA Visa"
  MERCADOPAGO: "mercadopago"         # Override default "Mercado Pago"
  # BBVA_MASTERCARD: "BBVA Mastercard" # Commented = use default
  # BBVA_ACCOUNT: "BBVA Account"       # Commented = use default
  # MACRO_ACCOUNT: "Macro Account"     # Commented = use default
```

Then use the config file:

```bash
PYTHONPATH=src uv run python -m cli.main --config config/development.yaml batch input/
```

### 2. Environment Variables

Use `FSP_PAYMENT_METHOD_*` environment variables:

```bash
# Single override
FSP_PAYMENT_METHOD_MACRO_VISA="MACRO VISA" PYTHONPATH=src uv run python -m cli.main batch input/

# Multiple overrides
FSP_PAYMENT_METHOD_MACRO_VISA="MACRO VISA" \
FSP_PAYMENT_METHOD_MERCADOPAGO="mercadopago" \
PYTHONPATH=src uv run python -m cli.main batch input/
```

Available environment variables:

- `FSP_PAYMENT_METHOD_MACRO_VISA`
- `FSP_PAYMENT_METHOD_BBVA_VISA`
- `FSP_PAYMENT_METHOD_BBVA_MASTERCARD`
- `FSP_PAYMENT_METHOD_BBVA_ACCOUNT`
- `FSP_PAYMENT_METHOD_MACRO_ACCOUNT`
- `FSP_PAYMENT_METHOD_MERCADOPAGO`

## Configuration Priority

The system follows this priority order:

1. YAML configuration file (if using `--config`)
2. Environment variables (FSP_PAYMENT_METHOD_*)
3. Default PaymentMethod enum values

## Examples

### Example 1: Uppercase Bank Names

```yaml
payment_method_mapping:
  MACRO_VISA: "MACRO VISA"
  BBVA_VISA: "BBVA VISA"
  BBVA_MASTERCARD: "BBVA MASTERCARD"
```

### Example 2: Lowercase Brands

```yaml
payment_method_mapping:
  MERCADOPAGO: "mercadopago"
  BBVA_ACCOUNT: "bbva account"
```

### Example 3: Custom Abbreviations

```yaml
payment_method_mapping:
  MACRO_VISA: "MV"
  BBVA_VISA: "BV"
  BBVA_MASTERCARD: "BMC"
  BBVA_ACCOUNT: "BA"
  MACRO_ACCOUNT: "MA"
  MERCADOPAGO: "MP"
```

## Important Notes

1. **Enum Names**: Use the exact PaymentMethod enum names (e.g., `MACRO_VISA`, not `Macro Visa`)
2. **Display Only**: This only affects the "Payment Method" column in Excel reports
3. **Business Logic**: Internal business logic continues to use the original enum values
4. **Partial Configuration**: You only need to specify the payment methods you want to customize
5. **Case Sensitive**: Environment variable names must be exact (FSP_PAYMENT_METHOD_MACRO_VISA)

## Testing Your Configuration

To verify your mapping configuration:

1. Process a statement file:

```bash
PYTHONPATH=src uv run python -m cli.main --config config/development.yaml process input/statement.pdf
```

2. Check the generated Excel file - the "Payment Method" column will show your custom names

3. Use environment variables for testing:

```bash
FSP_PAYMENT_METHOD_MACRO_VISA="TEST NAME" PYTHONPATH=src uv run python -m cli.main process input/statement.pdf
```

## Use Cases

- **Corporate Reporting**: Match company naming conventions
- **Data Integration**: Align with existing systems' naming schemes
- **User Preference**: Customize for readability (e.g., all caps, lowercase)
- **Internationalization**: Prepare for future multi-language support
- **Abbreviated Reports**: Use short codes for compact reports

The feature provides flexibility while maintaining the system's internal consistency and reliability.
