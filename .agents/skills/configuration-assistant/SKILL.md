---
name: configuration-assistant
description: Help configure this financial statement processor by reviewing its YAML settings, clarifying desired behavior, and presenting an agreed configuration before processing statements.
---

# Configuration assistant

Help the user choose settings for this repository's financial statement processor. Use the repository's configuration loader and call sites as the source of truth; distinguish settings that currently affect processing from settings that are only parsed, displayed, or unused. Do not promise behavior that the code does not implement.

## Workflow

1. Locate the user's selected YAML configuration, or ask which one to use if none is clear. The local `config/local-statements.yaml`, when available, is a useful starting reference; treat it as private and never quote, copy, or expose personal paths or other values in logs, chat, commits, or generated examples. Do not edit it unless explicitly asked.
2. Review the current values and ask focused, iterative questions about the choices that matter. Explain the practical effect of each choice plainly. Keep unknown or sensitive values private; ask about preferences without echoing them unnecessarily.
3. Classify each setting against current code. For this repository, `input_directory` and `output_directory` determine defaults for CLI input/output; `processing.enable_validation` controls validation; `processing.enable_balance_checking` controls balance reconciliation; `processing.duplicate_prefix` labels detected duplicates; `output.decimal_separator` changes decimal formatting in the Excel output; `payment_method_mapping` changes payment-method display labels; and `amount_sign_inversion` can invert amounts by method. `log_level` is loaded and shown by `info`, while verbose mode sets debug logging. `processing.max_workers`, `processing.retry_attempts`, `output.default_format`, and `output.date_format` are accepted in YAML but currently do not control processing/output behavior. Recheck source call sites before advising, since implementation can change.
4. Optionally inspect a consolidated Excel workbook if the user offers or selects one as a structural reference. Limit inspection to workbook/sheet names, column names/order, and non-transactional formatting or layout cues. Do not read, quote, summarize, or expose transaction rows or values. If structural inspection cannot be done without accessing transaction content, skip the workbook and say so.
5. Before processing any statements, present a concise proposed configuration summary with each requested change and its effective or currently inactive status, then ask the user to confirm the settings. Do not start processing until the user confirms.
6. After confirmation, make only the requested configuration changes, preserve unrelated YAML entries, and report the resulting file location and any settings that currently have no effect.
