"""Expected configuration loading failures."""


class ConfigError(Exception):
    """Base class for configuration loading errors."""


class ConfigFileError(ConfigError):
    """The configuration file cannot be read."""


class ConfigParseError(ConfigError):
    """The configuration file does not contain a usable YAML document."""


class ConfigValidationError(ConfigError):
    """The YAML document does not match the application model."""
