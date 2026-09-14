"""The shared EnergiMetrics namespace can include another distribution."""

import importlib
import sys
from pathlib import Path

import energimetrics
import energimetrics.helpers
from energimetrics.helpers.config import ConfigLoader


def test_namespace_levels_are_implicit() -> None:
    root_spec = energimetrics.__spec__
    helpers_spec = energimetrics.helpers.__spec__
    assert root_spec is not None and root_spec.origin is None
    assert helpers_spec is not None and helpers_spec.origin is None


def test_sibling_helper_from_another_path(tmp_path: Path) -> None:
    sibling = tmp_path / "energimetrics" / "helpers" / "mqtt"
    sibling.mkdir(parents=True)
    (sibling / "__init__.py").write_text(
        "CLIENT_NAME = 'MQTTClient'\n", encoding="utf-8"
    )
    sys.path.insert(0, str(tmp_path))
    importlib.invalidate_caches()
    try:
        mqtt = importlib.import_module("energimetrics.helpers.mqtt")
        assert mqtt.CLIENT_NAME == "MQTTClient"
        assert ConfigLoader.__module__ == "energimetrics.helpers.config.loader"
    finally:
        sys.modules.pop("energimetrics.helpers.mqtt", None)
        sys.path.remove(str(tmp_path))
        importlib.invalidate_caches()
