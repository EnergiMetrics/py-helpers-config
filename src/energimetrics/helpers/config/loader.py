"""Load YAML into a caller-supplied Pydantic model."""

from pathlib import Path

import yaml
from loguru import logger
from pydantic import BaseModel, ValidationError

from .exceptions import ConfigFileError, ConfigParseError, ConfigValidationError


class ConfigLoader[T: BaseModel]:
    """Load one YAML file as the supplied application model."""

    def __init__(self, path: str | Path, model: type[T]) -> None:
        self._path = Path(path)
        self._model = model

    @property
    def path(self) -> Path:
        """The configured file path."""
        return self._path

    def load(self) -> T:
        """Read, parse, and validate the configured YAML file."""
        logger.debug("Loading configuration from {}", self._path)
        self._validate_path()
        raw_config = self._load_yaml()
        logger.debug("Validating configuration from {}", self._path)
        try:
            config = self._model.model_validate(raw_config)
        except ValidationError as exc:
            lines: list[str] = []
            for issue in exc.errors(
                include_input=False, include_context=False, include_url=False
            ):
                location = ".".join(str(part) for part in issue["loc"]) or "<root>"
                lines.append(f"- {location}: {issue['msg']}")
            details = "\n".join(lines)
            error = ConfigValidationError(
                f"Configuration validation failed:\n{details}"
            )
            logger.error("{}", error)
            raise error from exc

        logger.info("Configuration loaded and validated: {}", self._path)
        return config

    def _validate_path(self) -> None:
        if not self._path.exists():
            error = ConfigFileError(f"Configuration file does not exist: {self._path}")
            logger.error("{}", error)
            raise error
        if not self._path.is_file():
            error = ConfigFileError(f"Configuration path is not a file: {self._path}")
            logger.error("{}", error)
            raise error

    def _load_yaml(self) -> object:
        try:
            contents = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            error = ConfigFileError(f"Cannot read configuration file: {self._path}")
            logger.error("{}", error)
            raise error from exc
        except UnicodeError as exc:
            error = ConfigFileError(
                f"Configuration file is not valid UTF-8: {self._path}"
            )
            logger.error("{}", error)
            raise error from exc

        logger.debug("Parsing YAML configuration from {}", self._path)
        try:
            data: object = yaml.safe_load(contents)
        except yaml.YAMLError as exc:
            error = ConfigParseError(
                f"Invalid YAML in configuration file: {self._path}"
            )
            logger.error("{}", error)
            raise error from exc

        if data is None:
            error = ConfigParseError(f"Configuration file is empty: {self._path}")
            logger.error("{}", error)
            raise error
        self._validate_root(data)
        return data

    def _validate_root(self, data: object) -> None:
        if not isinstance(data, dict):
            error = ConfigParseError(
                f"Configuration root must be a mapping: {self._path}"
            )
            logger.error("{}", error)
            raise error
