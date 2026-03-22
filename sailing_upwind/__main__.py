"""Command-line entry point: ``python -m sailing_upwind``.

Configuration is managed by Hydra. Override any value from the command line, e.g.::

    python -m sailing_upwind wind.speed_ms=6.0
    python -m sailing_upwind model.mode=two_deflector
    python -m sailing_upwind boat.sail_area_m2=7.0 model.centreboard.aspect_ratio=8.0
"""

from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from .plots import (
    plot_upwind_speed,
    plot_ds_sensitivity,
    plot_two_deflector_speed,
    plot_centreboard_sensitivity,
)
from .diagrams import plot_all_diagrams


@hydra.main(config_path="..", config_name="config", version_base="1.3")
def main(hydra_cfg: DictConfig) -> None:
    Path("img").mkdir(exist_ok=True)
    cfg = OmegaConf.to_container(hydra_cfg, resolve=True)

    plot_upwind_speed(cfg=cfg, show=False, save=True)
    plot_ds_sensitivity(cfg=cfg, show=False, save=True)
    plot_two_deflector_speed(cfg=cfg, show=False, save=True)
    plot_centreboard_sensitivity(cfg=cfg, show=False, save=True)
    plot_all_diagrams(cfg=cfg, show=False, save=True)


if __name__ == "__main__":
    main()
