"""Load and validate the YAML configuration file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG = Path(__file__).parent.parent / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the YAML config and return it as a nested dict.

    Parameters
    ----------
    path:
        Path to a YAML config file.  Defaults to ``config.yaml`` in the
        repository root.

    Returns
    -------
    dict
        Validated configuration dictionary.

    Examples
    --------
    >>> cfg = load_config()
    >>> cfg["wind"]["speed_ms"]
    4.0
    >>> cfg["coefficients"]["D_s"]
    0.895
    """
    config_path = Path(path) if path is not None else _DEFAULT_CONFIG
    with config_path.open() as fh:
        cfg = yaml.safe_load(fh)
    _validate(cfg)
    return cfg


def _validate(cfg: dict[str, Any]) -> None:
    """Raise ValueError if any required key is missing or out of range."""
    required = {
        "boat": ["sail_area_m2", "hull_area_m2"],
        "wind": ["speed_ms"],
        "coefficients": ["D_s", "D_h"],
        "fluid": ["rho_air_kg_m3", "rho_water_kg_m3"],
    }
    for section, keys in required.items():
        if section not in cfg:
            raise ValueError(f"Config missing section '{section}'")
        for key in keys:
            if key not in cfg[section]:
                raise ValueError(f"Config missing '{section}.{key}'")

    D_s = cfg["coefficients"]["D_s"]
    D_h = cfg["coefficients"]["D_h"]
    if not (0.0 < D_s < 1.0):
        raise ValueError(f"D_s must be in (0, 1), got {D_s}")
    if not (0.0 < D_h < 1.0):
        raise ValueError(f"D_h must be in (0, 1), got {D_h}")
    if cfg["wind"]["speed_ms"] <= 0:
        raise ValueError("wind.speed_ms must be positive")
    if cfg["boat"]["sail_area_m2"] <= 0:
        raise ValueError("boat.sail_area_m2 must be positive")
    if cfg["boat"]["hull_area_m2"] <= 0:
        raise ValueError("boat.hull_area_m2 must be positive")
