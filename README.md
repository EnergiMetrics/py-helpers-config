# EnergiMetrics Config Helper

YAML configuration loading and Pydantic validation for EnergiMetrics Python applications.

Install directly from GitHub with `uv`:

```bash
uv add "energimetrics.helpers.config @ git+https://github.com/EnergiMetrics/py-helpers-config.git"
```

Applications should prefer a tagged version when one is available:

```bash
uv add "energimetrics.helpers.config @ git+https://github.com/EnergiMetrics/py-helpers-config.git@v0.1.0"
```

Define the schema in the consuming application, then load its YAML file:

```python
from pydantic import BaseModel

from energimetrics.helpers.config import ConfigLoader


class AppConfig(BaseModel):
    name: str
    debug: bool = False


config = ConfigLoader("config.yaml", AppConfig).load()
print(config.name)
```

`config` has the exact type `AppConfig`, including its fields in static analysis and IDE autocomplete. The helper does not define application-specific models.

Catch any expected loading failure with `ConfigError`:

```python
from energimetrics.helpers.config import ConfigError, ConfigLoader

try:
    config = ConfigLoader("config.yaml", AppConfig).load()
except ConfigError as exc:
    print(f"Cannot load configuration: {exc}")
```

`ConfigFileError`, `ConfigParseError`, and `ConfigValidationError` are available for callers that need more specific handling. Validation failures list readable field paths. The package emits Loguru messages but leaves logging configuration to the application and never logs the loaded model.

The distribution and import path are both `energimetrics.helpers.config`. EnergiMetrics uses the shared `energimetrics.helpers.*` namespace for reusable Python helper libraries.

For development, run `uv sync --locked`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`.
