"""Static contract checked by Pyright, not a runtime test."""

from pathlib import Path
from typing import assert_type

from pydantic import BaseModel

from energimetrics.helpers.config import ConfigLoader


class ApplicationConfig(BaseModel):
    name: str


def check_inferred_model_type(path: Path) -> None:
    config = ConfigLoader(path, ApplicationConfig).load()
    assert_type(config, ApplicationConfig)
    assert_type(config.name, str)
