"""Sailing upwind optimisation model.

Based on a high-school coursework model that derives the optimum angle to
sail upwind for a simple dinghy.  See ``coursework.txt`` for the full
derivation and ``config.yaml`` for tuneable parameters.
"""

from .model import boat_speed, upwind_speed, optimal_angle, no_go_threshold
from .config import load_config

__all__ = [
    "boat_speed",
    "upwind_speed",
    "optimal_angle",
    "no_go_threshold",
    "load_config",
]
