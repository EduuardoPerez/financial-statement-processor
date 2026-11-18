# Financial Statement Processor

CLI para convertir extractos bancarios en transacciones estructuradas y archivos
Excel. El código de aplicación está organizado en `src/domain`, `src/application`,
`src/infrastructure` y `src/cli`.

## Requisitos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/)

## Instalación

```bash
uv sync
```

## Uso

```bash
# Ver formatos y métodos de pago reconocidos
PYTHONPATH=src uv run python -m cli.main info

# Procesar un archivo
PYTHONPATH=src uv run python -m cli.main process /ruta/al/extracto.pdf

# Validar un archivo sin generar la salida
PYTHONPATH=src uv run python -m cli.main validate /ruta/al/extracto.pdf

# Procesar los archivos compatibles de una carpeta
PYTHONPATH=src uv run python -m cli.main batch /ruta/a/extractos/

# Consolidar transacciones de una carpeta
PYTHONPATH=src uv run python -m cli.main consolidate /ruta/a/extractos/
```

Se puede indicar una configuración YAML con `--config` antes del comando. Sin
esa opción, la CLI lee variables de entorno con prefijo `FSP_`. Los valores
disponibles y sus valores predeterminados están definidos en
`src/infrastructure/config.py`; `config/development.yaml` y
`config/production.yaml` son ejemplos.
Para personalizar los nombres de métodos de pago, consulta
[`docs/PAYMENT_METHOD_MAPPING.md`](docs/PAYMENT_METHOD_MAPPING.md).

Los archivos procesados se guardan en `output/` por defecto. Los directorios
`input/`, `output/` y `expected_output/` son locales de trabajo y están excluidos
de Git. No guardes extractos personales en el repositorio. Las muestras
necesarias para las pruebas se mantienen bajo `tests/test_data/`.

## Desarrollo

```bash
uv sync
uv run pytest
uv run ruff check src tests --ignore=E501
uv run ruff format --check src tests
uv run mypy src/
```

Ruff y mypy se ejecutan en los hooks de pre-commit. La suite de pytest se ejecuta
en GitHub Actions para no alargar cada commit local.
