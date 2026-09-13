"""Behavioral tests for YAML configuration loading."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from energimetrics_config_helper import (
    ConfigError,
    ConfigFileError,
    ConfigLoader,
    ConfigParseError,
    ConfigValidationError,
)


class Sensor(BaseModel):
    pin: int


class AppConfig(BaseModel):
    name: str
    sensors: list[Sensor]
    debug: bool = False


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text("name: demo\nsensors:\n  - pin: 7\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("as_string", [False, True])
def test_load_returns_supplied_model_with_nested_and_default_fields(
    config_file: Path, as_string: bool
) -> None:
    path = str(config_file) if as_string else config_file
    loader = ConfigLoader(path, AppConfig)

    result = loader.load()

    assert type(result) is AppConfig
    assert result.name == "demo"
    assert result.sensors[0].pin == 7
    assert result.debug is False
    assert loader.path == config_file


def test_missing_file_is_config_file_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigFileError, match="does not exist") as caught:
        ConfigLoader(tmp_path / "missing.yaml", AppConfig).load()
    assert isinstance(caught.value, ConfigError)


def test_directory_is_config_file_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigFileError, match="not a file"):
        ConfigLoader(tmp_path, AppConfig).load()


def test_read_failure_is_chained(config_file: Path) -> None:
    with (
        patch.object(Path, "read_text", side_effect=OSError("permission denied")),
        pytest.raises(ConfigFileError, match="Cannot read") as caught,
    ):
        ConfigLoader(config_file, AppConfig).load()
    assert isinstance(caught.value.__cause__, OSError)


def test_invalid_utf8_is_chained(config_file: Path) -> None:
    config_file.write_bytes(b"\xff")
    with pytest.raises(ConfigFileError, match="valid UTF-8") as caught:
        ConfigLoader(config_file, AppConfig).load()
    assert isinstance(caught.value.__cause__, UnicodeError)


@pytest.mark.parametrize("contents", ["", "# comment only\n"])
def test_empty_document_is_rejected(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ConfigParseError, match="empty"):
        ConfigLoader(path, AppConfig).load()


def test_malformed_yaml_is_chained(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("name: [unfinished\n", encoding="utf-8")
    with pytest.raises(ConfigParseError, match="Invalid YAML") as caught:
        ConfigLoader(path, AppConfig).load()
    assert caught.value.__cause__ is not None


@pytest.mark.parametrize("contents", ["hello\n", "- one\n- two\n", "42\n"])
def test_root_must_be_mapping(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ConfigParseError, match="root must be a mapping"):
        ConfigLoader(path, AppConfig).load()


def test_missing_required_field_has_readable_path(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("sensors: []\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="- name: Field required") as caught:
        ConfigLoader(path, AppConfig).load()
    assert caught.value.__cause__ is not None


def test_nested_and_multiple_validation_errors_are_readable(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("name: demo\nsensors:\n  - {}\n  - pin: nope\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError) as caught:
        ConfigLoader(path, AppConfig).load()
    message = str(caught.value)
    assert "- sensors.0.pin: Field required" in message
    assert "- sensors.1.pin: Input should be a valid integer" in message
    assert "input_value" not in message


def test_secret_value_is_not_logged_or_in_error(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("name: demo\nsensors: secret-token\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError) as caught:
        ConfigLoader(path, AppConfig).load()
    assert "secret-token" not in str(caught.value)
